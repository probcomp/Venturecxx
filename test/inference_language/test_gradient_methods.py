from testconfig import config
from venture.test.config import get_ripl, collectSamples
from itertools import product
from nose import SkipTest
from nose.tools import assert_almost_equal

def testGradientMethodsBasic():
  "Run tests over both gradient methods"
  tests = (checkGradientMethodsBasic,)
  methods = ("map", "nesterov")
  for test, method in product(tests, methods):
    yield test, method

def checkGradientMethodsBasic(inference_method):
  "Make sure that map methods find the maximum"
  if config["get_ripl"] != "lite": raise SkipTest("Gradient climbers only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(normal 1 1)", label = "pid")
  ripl.force("a", 0.0)
  infer_statement = "({0} default all 0.1 10 20)".format(inference_method)
  prediction = collectSamples(ripl, "pid", infer = infer_statement,
                              num_samples = 1)[0]
  assert_almost_equal(prediction, 1)

def testNesterovWithInt():
  "Without fixing VentureInteger to play nicely with Python numbers, this errors"
  if config["get_ripl"] != "lite": raise SkipTest("Gradient climbers only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume('x', '(normal 1 1)')
  ripl.force('x', 0)
  ripl.infer('(nesterov default one 0.1 10 20)')
