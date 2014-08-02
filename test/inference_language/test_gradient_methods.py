from nose.tools import assert_almost_equal
from nose import SkipTest

from venture.test.config import get_ripl, collectSamples, broken_in, gen_broken_in, on_inf_prim, gen_on_inf_prim

@gen_broken_in('puma', "Gradient climbers only implemented in Lite.")
@gen_on_inf_prim("map")
def testGradientMethodsBasicMap():
  yield checkGradientMethodsBasic, "map"

@gen_broken_in('puma', "Gradient climbers only implemented in Lite.")
@gen_on_inf_prim("nesterov")
def testGradientMethodsBasicNesterov():
  yield checkGradientMethodsBasic, "nesterov"

def checkGradientMethodsBasic(inference_method):
  "Make sure that map methods find the maximum"
  ripl = get_ripl()
  ripl.assume("a", "(normal 1 1)", label = "pid")
  ripl.force("a", 0.0)
  infer_statement = "({0} default all 0.1 10 20)".format(inference_method)
  prediction = collectSamples(ripl, "pid", infer = infer_statement,
                              num_samples = 1)[0]
  assert_almost_equal(prediction, 1)

@broken_in('puma', "Gradient climbers only implemented in Lite.")
@on_inf_prim("nesterov")
def testNesterovWithInt():
  "Without fixing VentureInteger to play nicely with Python numbers, this errors"
  raise SkipTest("Observes that change the type of a variable may break gradient methods. Issue: https://app.asana.com/0/11127829865276/15085515046349")
  ripl = get_ripl()
  ripl.assume('x', '(normal 1 1)')
  ripl.force('x', 0)
  ripl.infer('(nesterov default one 0.1 10 20)')
