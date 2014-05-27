import os

import numpy as np
import scipy.io

import venture.shortcuts as shortcuts
from lda import LDA

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

    history, ripl = model.runFromConditional(200, verbose=True, data=data)
