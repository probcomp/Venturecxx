from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim, broken_in, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

@gen_on_inf_prim("none")
def testDirSmoke():
  yield checkDirSmoke1, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke2, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke1, "(dirichlet (array 3 3 3 3))"
  yield checkDirSmoke2, "(dirichlet (array 3 3 3 3))"

def checkDirSmoke1(form):
  eq_(get_ripl().predict("(is_simplex %s)" % form), True)

def checkDirSmoke2(form):
  eq_(get_ripl().predict("(size %s)" % form), 4)

@on_inf_prim("none")
def testDirichletComparisonRegression():
  eq_(get_ripl().predict("(= (symmetric_dirichlet 3 2) (simplex 0.01 0.99))"), False) # As opposed to crashing

@broken_in('puma', "Puma does not define log_flip")
@statisticalTest
def testLogFlip():
  ripl = get_ripl()
  
  ripl.predict('(log_flip (log 0.5))', label='pid')
  
  predictions = collectSamples(ripl,'pid')
  ans = [(False,0.5),(True,0.5)]
  return reportKnownDiscrete(ans, predictions)

