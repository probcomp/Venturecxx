from scipy import stats

from venture.test.config import get_ripl, broken_in
from venture.exception import underline
from venture.lite.psp import LikelihoodFreePSP
from venture.lite import value as v
from venture.lite.builtin import typed_nr

@broken_in('puma', "Profiler only implemented for Lite")
def test_profiling1():
  ripl = get_ripl()

  ripl.execute_program("""
    [assume tricky (scope_include (quote tricky) 0 (flip 0.5))]
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
  tester = typed_nr(TestPSP(), [v.NumberType()], v.NumberType())
  ripl = get_ripl()
  ripl.bind_foreign_sp('test', tester)
  prog = '''
  [ASSUME x (test 0)]
  [INFER (mh default one 10)]'''
  ripl.profiler_enable()
  ripl.execute_program(prog)

