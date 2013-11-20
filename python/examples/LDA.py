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


def makeAssumes(my_ripl, parameters):
    my_ripl.assume("topics", str(parameters['topics']))
    my_ripl.assume("vocab", str(parameters['vocab']))
    my_ripl.assume("alpha_document_topic", "(gamma 1.0 1.0)")
    my_ripl.assume("alpha_topic_word", "(gamma 1.0 1.0)")
    my_ripl.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
    my_ripl.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
    my_ripl.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")


def makeObserves(my_ripl, parameters):
    D = parameters['documents']
    N = parameters['words_per_document']
    for doc in xrange(D):
        for pos in xrange(N):
            my_ripl.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
    return


def main():
    my_ripl = shortcuts.make_church_prime_ripl() 
    parameters = {'topics' : 4, 'vocab' : 10, 'documents' : 8, 'words_per_document': 8}
    makeAssumes(my_ripl, parameters)
    makeObserves(my_ripl, parameters)
    my_ripl.infer({'transitions': 10})
    return my_ripl, parameters


if __name__ == '__main__':
    my_ripl, parameters = main()
