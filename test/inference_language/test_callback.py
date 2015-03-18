import numbers
from nose.tools import eq_

import venture.lite.value as v
from venture.test.config import get_ripl
from venture.engine.inference import Infer

def testCallbackSmoke():
  class MyCallback(object):
    def __init__(self):
      self.call_ct = 0
    def __call__(self, inferrer, *sampless):
      assert isinstance(inferrer, Infer)
      eq_(len(sampless), 2) # Two expressions
      for samples in sampless:
        eq_(len(samples), 4) # Four particles
        for sample in samples:
          assert isinstance(sample, dict) # A stack dict holding a number
          eq_(sample["type"], "number")
          assert isinstance(sample["value"], numbers.Number)
      self.call_ct += 1
  my_callback = MyCallback()

  ripl = get_ripl()
  ripl.bind_callback("foo", my_callback)
  ripl.execute_program("""
[infer (resample 4)]
[assume x (normal 0 1)]
[infer (repeat 3 (call_back foo x (gamma 1 1)))]""")
  eq_(my_callback.call_ct, 3)

def testCallbackReturns():
  ripl = get_ripl()
  ripl.bind_callback("three", lambda _inferrer: v.VentureNumber(3))
  ripl.infer("(do (x <- (call_back three)) (assert (eq 3 x)))")
