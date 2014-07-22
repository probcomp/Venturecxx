# Copyright (c) 2013, MIT Probabilistic Computing Project.
# 
# This file is part of Venture.
# 	
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 	
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 	
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from venture import shortcuts
from venture.unit import VentureUnit, productMap, plotAsymptotics

class LDA(VentureUnit):
    def makeAssumes(self):
        self.assume("topics", self.parameters['topics'])
        self.assume("vocab", self.parameters['vocab'])
        self.assume("alpha_document_topic", "(gamma 1.0 1.0)")
        self.assume("alpha_topic_word", "(gamma 1.0 1.0)")
        self.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
        self.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
        self.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")
        return


    def makeObserves(self):
        D = self.parameters['documents']
        N = self.parameters['words_per_document']
        for doc in range(D):
            for pos in range(N):
                self.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
        return


ripl = shortcuts.Lite().make_church_prime_ripl()
#parameters = {'topics' : 4, 'vocab' : 10, 'documents' : 8, 'words_per_document' : 12}

#model = LDA(ripl, parameters)
#history = model.runConditionedFromPrior(50, verbose=True)
#history = model.runFromJoint(50, verbose=True)
#history = model.sampleFromJoint(20, verbose=True)
#sample_hist, infer_hist, klHistory = model.computeJointKL(20, 10, verbose=True)
#history = model.runFromConditional(50)
#klHistory.plot(fmt='png')

parameters = {'topics' : [4], 'vocab' : [2**n for n in range(10)], 'documents' : [8], 'words_per_document' : [10]}
def runner(params):
    print params
    return LDA(ripl, params).runFromJoint(10, verbose=True, runs=1)
histories = productMap(parameters, runner)
#
plotAsymptotics(parameters, histories, 'sweep time (s)', fmt='png', aggregate=False)
