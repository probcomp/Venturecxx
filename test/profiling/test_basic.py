# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from scipy import stats

from venture.test.config import get_ripl, broken_in
from venture.exception import underline
from venture.lite.psp import LikelihoodFreePSP
from venture.lite import types as t
from venture.lite.builtin import typed_nr

@broken_in('puma', "Profiler only implemented for Lite")
def test_profiling1():
  ripl = get_ripl()

  ripl.execute_program("""
    [assume tricky (tag (quote tricky) 0 (flip 0.5))]
    [assume weight (if tricky (uniform_continuous 0 1) 0.5)]
    [assume coin (lambda () (flip weight))]
    [observe (coin) true]
    [observe (coin) true]
    [observe (coin) true]
  """)

  ripl.profiler_enable()
  ripl.infer('(mh default one 10)')
  ripl.infer('(gibbs tricky one 1)')

  def printAddr((did, index)):
    exp = ripl.sivm._get_exp(did)
    text, indyces = ripl.humanReadable(exp, did, index)
    print text
    print underline(indyces)

  data = ripl.profile_data()

  assert len(data) == 11

  map(lambda addrs: map(printAddr, addrs), data.principal)

@broken_in('puma', "Profiler only implemented for Lite")
def test_profiling_likelihoodfree():
  "Make sure profiling doesn't break with likelihood-free SP's"
  class TestPSP(LikelihoodFreePSP):
    def simulate(self, args):
      x = args.operandValues[0]
      return x + stats.distributions.norm.rvs()
  tester = typed_nr(TestPSP(), [t.NumberType()], t.NumberType())
  ripl = get_ripl()
  ripl.bind_foreign_sp('test', tester)
  prog = '''
  [ASSUME x (test 0)]
  [INFER (mh default one 10)]'''
  ripl.profiler_enable()
  ripl.execute_program(prog)

