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
        N = self.parameters['words_per_document']
        if isinstance(N, int):
            N = [N] * D
        # TODO: use bulk_observe or observe_dataset (not yet implemented in VentureUnit)
        for doc in range(D):
            for pos in range(N[doc]):
                self.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
        return

if __name__ == '__main__':
    mat = scipy.io.loadmat(os.path.join(os.path.dirname(__file__), 'nips_1-17.mat'))
    counts = mat['counts']
    n_words, n_docs = counts.shape
    doc_words = []
    words_per_doc = []
    for doc in range(n_docs):
        inds = counts.indices[counts.indptr[doc]:counts.indptr[doc+1]]
        cts = counts.data[counts.indptr[doc]:counts.indptr[doc+1]]
        doc_words.append(np.repeat(inds, cts))
        words_per_doc.append(np.sum(cts))
    data = ["atom<%d>" % d for d in np.concatenate(doc_words)]

    ripl = shortcuts.make_church_prime_ripl()
    parameters = {'topics': 300, 'vocab': n_words, 'documents': n_docs,
                  'words_per_document': words_per_doc}
    model = LDA(ripl, parameters)

    infer = "(cycle ((slice 0 one 20) (mh default one %d)) 1)" % counts.nnz
    history, ripl = model.runFromConditional(200, verbose=True, data=data, infer=infer)
