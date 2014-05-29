import os

import numpy as np
import scipy.io

import venture.shortcuts as shortcuts
from venture.unit import VentureUnit

class LDA(VentureUnit):
    def makeAssumes(self):
        self.assume("topics", self.parameters['topics'])
        self.assume("vocab", self.parameters['vocab'])
        self.assume("alpha_document_topic", "(scope_include 0 0 (gamma 1.0 1.0))")
        self.assume("alpha_topic_word", "(scope_include 0 1 (gamma 1.0 1.0))")
        self.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
        self.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
        self.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")
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
                      'doc_length': 25}
        iters = len(data)
    elif corpus.startswith('nips'):
        n_docs = corpus[4:]
        mat = scipy.io.loadmat(os.path.join(os.path.dirname(__file__), 'nips_1-17.mat'))
        counts = mat['counts']
        if n_docs:
            # truncate dataset
            counts = counts[:, :int(n_docs)]
        n_words, n_docs = counts.shape
        doc_words = []
        doc_lengths = []
        for doc in range(n_docs):
            inds = counts.indices[counts.indptr[doc]:counts.indptr[doc+1]]
            cts = counts.data[counts.indptr[doc]:counts.indptr[doc+1]]
            doc_words.append(np.repeat(inds, cts))
            doc_lengths.append(np.sum(cts))
        data = ["atom<%d>" % d for d in np.concatenate(doc_words)]
        parameters = {'topics': min(300, n_docs),
                      'vocab': n_words, 'documents': n_docs,
                      'doc_length': doc_lengths}
        iters = counts.sum()

    ripl = shortcuts.make_church_prime_ripl()
    model = LDA(ripl, parameters)

    infer = "(cycle ((slice 0 one 20) (mh default one %d)) 1)" % iters
    history, ripl = model.runFromConditional(200, verbose=True, data=data, infer=infer)
