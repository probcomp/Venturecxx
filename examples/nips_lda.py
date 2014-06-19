import os

import numpy as np
import scipy.io

import venture.shortcuts as shortcuts
from venture.unit import VentureUnit

class LDA(VentureUnit):
    def makeAssumes(self):
        self.assume("topics", self.parameters['topics'])
        self.assume("vocab", self.parameters['vocab'])
        self.assume("alpha_document_topic", "(scope_include 0 0 (gamma 1.0 topics))")
        self.assume("alpha_topic_word", "(scope_include 0 1 (gamma 1.0 vocab))")
        self.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
        self.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
        self.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler (scope_include 1 (+ pos (* 1000000 doc)) ((get_document_topic_sampler doc)))))))")
        return

    def makeObserves(self):
        D = self.parameters['documents']
        N = self.parameters['doc_length']
        if isinstance(N, int):
            N = [N] * D
        # TODO: use bulk_observe or observe_dataset (not yet implemented in VentureUnit)
        for doc in range(D):
            for pos in range(N[doc]):
                self.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
        return

    def makeQueryExps(self):
        D = self.parameters['documents']
        T = self.parameters['topics']
        for i in range(D):
            self.queryExp("(get_document_topic_sampler %d)" % i)
        for i in range(T):
            self.queryExp("(get_topic_word_sampler atom<%d>)" % i)

def unzip_dict(d):
    keys, valss = zip(*d.items())
    for vals in zip(*valss):
        yield dict(zip(keys, vals))

def normalize_counts(dir_mult, n):
    if dir_mult['type'] == 'sym_dir_mult':
        alpha = dir_mult['alpha']
        assert n == dir_mult['n']
        counts = dir_mult['counts']
    elif dir_mult['type'] == 'crp':
        alpha = dir_mult['alpha'] / n
        counts = [dir_mult['counts'].get(i, {'value': 0})['value'] for i in range(n)]
    else:
        raise ValueError
    total = sum(counts)
    return [(c + alpha) / (total + n * alpha) for c in counts]

def visualize_topic(dir_mult, words):
    counts = normalize_counts(dir_mult, len(words))
    for index, count in sorted(enumerate(counts), key=lambda x: -x[1])[:10]:
        print words[index], count

def visualize_topics(history, words):
    T = history.parameters['topics']
    topic_word_exps = ["(get_topic_word_sampler atom<%d>)" % i for i in range(T)]
    series = {}
    for name in topic_word_exps:
        series[name] = history.nameToSeries[name]
    ret = []
    for (i, run) in enumerate(unzip_dict(series)):
        print 'Run', i
        results = [run[name].values[-1] for name in topic_word_exps]
        for (t, dir_mult) in enumerate(results):
            print 'Topic', t
            visualize_topic(dir_mult, words)

def predicted_document_word_matrices(history):
    D = history.parameters['documents']
    T = history.parameters['topics']
    W = history.parameters['vocab']
    document_topic_exps = ["(get_document_topic_sampler %d)" % i for i in range(D)]
    topic_word_exps = ["(get_topic_word_sampler atom<%d>)" % i for i in range(T)]
    series = {}
    for name in document_topic_exps + topic_word_exps:
        series[name] = history.nameToSeries[name]
    ret = []
    for run in unzip_dict(series):
        run_ret = []
        for value_dict in unzip_dict(dict((n, s.values) for (n, s) in run.items())):
            document_topic_matrix = [normalize_counts(value_dict[name], T) for name in document_topic_exps]
            topic_word_matrix = [normalize_counts(value_dict[name], W) for name in topic_word_exps]
            document_word_matrix = np.dot(document_topic_matrix, topic_word_matrix)
            run_ret.append(document_word_matrix)
        label = next(run.itervalues()).label
        ret.append((label, run_ret))
    return ret

def actual_document_word_matrix(history):
    D = history.parameters['documents']
    N = history.parameters['doc_length']
    W = history.parameters['vocab']
    if isinstance(N, int):
        N = [N] * D
    counts = np.zeros((D, W))
    offset = 0
    for doc in range(D):
        for pos in range(N[doc]):
            datum = history.data[offset][1]
            if isinstance(datum, str):
                assert datum.startswith('atom<') and datum.endswith('>')
                word = int(datum[5:-1])
            else:
                assert isinstance(datum, dict) and datum['type'] == 'atom'
                word = datum['value']
            counts[doc, word] += 1
            offset += 1
    return counts

def add_diagnostics(history):
    N = history.parameters['doc_length']
    if isinstance(N, list):
        N = np.transpose([N])
    actual = actual_document_word_matrix(history)
    predictions = predicted_document_word_matrices(history)
    for label, run in predictions:
        errors = []
        sqerrs = []
        logscores = []
        for predicted in run:
            logscores.append(np.sum(actual * np.log(predicted)))
            errors.append(np.mean(np.abs(actual/N - predicted)))
            sqerrs.append(np.mean(np.square(actual/N - predicted)))
        history.addSeries('predictive logscore', 'number', label, logscores)
        history.addSeries('predictive mean error', 'number', label, errors)
        history.addSeries('predictive squared error', 'number', label, sqerrs)

if __name__ == '__main__':
    import sys
    try:
        corpus = sys.argv[1]
    except IndexError:
        print 'Usage: {0} [synth1|synth2|nips[n_docs]]'
        sys.exit()
    if corpus == 'synth1':
        docs = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
                0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
                0, 0, 0, 0, 1, 1, 1, 1, 3, 3, 3, 3,
                0, 0, 0, 0, 1, 1, 1, 1, 4, 4, 4, 4,
                4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6,
                4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6,
                7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9,
                7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9]
        data = ["atom<%d>" % x for x in docs]
        parameters = {'topics': 4, 'vocab': 10, 'documents': 8,
                      'doc_length': 12}
        iters = len(data)
    elif corpus == 'synth2':
        docs = [
            [22, 7, 29, 11, 25, 0, 4, 11, 5, 11,
             2, 11, 11, 2, 29, 28, 11, 23, 26, 5,
             11, 23, 2, 29, 12, 0, 29, 11, 11, 2,
             3, 11, 29, 4, 12, 1, 21, 11, 2, 29,
             11, 29, 29, 5, 4, 0, 11, 2, 21, 23],
            [18, 23, 0, 13, 27, 8, 29, 26, 24, 16,
             26, 17, 8, 4, 7, 22, 0, 21, 26, 2,
             7, 7, 7, 18, 13, 27, 12, 29, 2, 26,
             2, 26, 29, 15, 23, 23, 7, 17, 18, 26,
             17, 24, 22, 2, 26, 18, 20, 23, 17, 3],
            [23, 22, 23, 28, 7, 6, 26, 4, 23, 28,
             27, 14, 18, 18, 28, 23, 2, 23, 26, 2,
             28, 7, 0, 19, 26, 18, 22, 16, 18, 16,
             2, 2, 8, 22, 4, 21, 8, 15, 26, 23,
             8, 17, 6, 16, 29, 26, 8, 15, 22, 18],
            [29, 17, 16, 12, 19, 29, 26, 26, 17, 16,
             0, 29, 28, 7, 26, 23, 6, 17, 13, 0,
             2, 5, 7, 17, 12, 23, 14, 11, 21, 0,
             2, 23, 23, 2, 28, 4, 21, 21, 2, 23,
             11, 24, 29, 26, 18, 27, 12, 18, 23, 22],
            [26, 0, 18, 0, 5, 2, 2, 11, 7, 11,
             0, 3, 11, 11, 11, 11, 6, 0, 25, 29,
             0, 2, 29, 29, 5, 23, 7, 23, 11, 11,
             11, 22, 25, 23, 5, 7, 7, 18, 17, 11,
             2, 28, 12, 28, 28, 2, 2, 0, 11, 23],
            [29, 11, 11, 12, 8, 11, 11, 28, 11, 8,
             18, 3, 11, 3, 29, 5, 11, 23, 2, 2,
             11, 2, 11, 3, 2, 23, 17, 2, 12, 2,
             11, 11, 2, 11, 29, 14, 5, 2, 23, 5,
             11, 11, 16, 28, 12, 28, 11, 11, 11, 11],
            [28, 11, 11, 28, 2, 22, 7, 7, 7, 28,
             5, 22, 7, 6, 2, 22, 23, 28, 0, 26,
             7, 7, 7, 28, 22, 18, 23, 23, 23, 28,
             0, 23, 21, 17, 22, 23, 17, 22, 24, 11,
             0, 22, 28, 5, 18, 25, 23, 5, 11, 29],
            [22, 8, 23, 27, 26, 6, 5, 17, 17, 18,
             8, 26, 28, 22, 16, 23, 18, 2, 7, 8,
             26, 23, 28, 7, 18, 11, 7, 2, 4, 17,
             24, 22, 27, 7, 23, 17, 12, 26, 8, 8,
             7, 16, 23, 26, 0, 17, 16, 27, 7, 7]
        ]
        data = ["atom<%d>" % x for doc in docs for x in doc]
        parameters = {'topics': 4, 'vocab': 30, 'documents': 8,
                      'doc_length': 50}
        iters = len(data)
    elif corpus == 'prior':
        data = None
        parameters = {'topics': int(sys.argv[2]), 'vocab': int(sys.argv[3]),
                      'documents': int(sys.argv[4]),
                      'doc_length': int(sys.argv[5])}
        iters = parameters['documents'] * parameters['doc_length']
    elif corpus == 'nips_sample':
        n_topics = int(sys.argv[2])
        n_words = int(sys.argv[3])
        n_docs = int(sys.argv[4])
        doc_length = int(sys.argv[5])
        mat = scipy.io.loadmat(os.path.join(os.path.dirname(__file__), 'nips_1-17.mat'))
        words = mat['words']
        counts = mat['counts']
        if n_docs > 0:
            # take only first n docs
            counts = counts[:, :n_docs]
        if n_words > 0:
            # take only most common n words
            word_freqs = np.ravel(counts.astype('uint32').sum(axis=1))
            most_freq_words = word_freqs.argpartition(-n_words)[-n_words:]
            words = words[:, most_freq_words]
            counts = counts[most_freq_words, :]
        n_words, n_docs = counts.shape
        doc_words = []
        doc_lengths = []
        for doc in range(n_docs):
            inds = counts.indices[counts.indptr[doc]:counts.indptr[doc+1]]
            cts = counts.data[counts.indptr[doc]:counts.indptr[doc+1]]
            wds = np.repeat(inds, cts)
            if doc_length > 0:
                # randomly sample n words from the document
                wds = np.random.choice(wds, doc_length)
            doc_words.append(wds)
            doc_lengths.append(wds.size)
        data = ["atom<%d>" % d for d in np.concatenate(doc_words)]
        parameters = {'topics': n_topics,
                      'vocab': n_words, 'documents': n_docs,
                      'doc_length': doc_length if doc_length > 0 else doc_lengths}
        iters = sum(doc_lengths)
    elif corpus == 'nips':
        n_topics = int(sys.argv[2])
        n_docs = int(sys.argv[3])
        mat = scipy.io.loadmat(os.path.join(os.path.dirname(__file__), 'nips_1-17.mat'))
        counts = mat['counts'][:, :n_docs]
        n_words, n_docs = counts.shape
        doc_words = []
        doc_lengths = []
        for doc in range(n_docs):
            inds = counts.indices[counts.indptr[doc]:counts.indptr[doc+1]]
            cts = counts.data[counts.indptr[doc]:counts.indptr[doc+1]]
            doc_words.append(np.repeat(inds, cts))
            doc_lengths.append(np.sum(cts))
        data = ["atom<%d>" % d for d in np.concatenate(doc_words)]
        parameters = {'topics': n_topics,
                      'vocab': n_words, 'documents': n_docs,
                      'doc_length': doc_lengths}
        iters = counts.sum()

    ripl = shortcuts.make_church_prime_ripl()
    model = LDA(ripl, parameters)

    infer = "(cycle ((mh 0 one 2) (gibbs 1 one %d)) 1)" % iters
    if corpus == 'prior':
        history, ripl = model.runConditionedFromPrior(200, verbose=True, infer=infer)
    else:
        history, ripl = model.runFromConditional(200, verbose=True, data=data, infer=infer)

    add_diagnostics(history)
