import numpy as np
from nose.tools import eq_, assert_almost_equal
from nose.plugins.attrib import attr

from venture.test.config import get_ripl, on_inf_prim
import venture.lite.continuous as cont
from venture.lite.builtin import typed_nr
import venture.lite.value as v

@attr("slow")
@on_inf_prim("emap")
def testVentureScriptAbstractExample():
  class EnumerableUniformOutputPSP(cont.UniformOutputPSP):
    def canEnumerate(self): return True
    def enumerateValues(self, args):
      (low, high) = args.operandValues
      return np.arange(low, high, (high-low)/100)

  r = get_ripl()
  r.set_mode("venture_script")
  r.bind_foreign_sp("uniform_continuous", typed_nr(EnumerableUniformOutputPSP(), [v.NumberType(), v.NumberType()], v.NumberType()))
  r.execute_program("""
infer resample(2)
assume is_funny = scope_include(quote(fun), 0, flip(0.3))
assume funny_mean = scope_include(quote(mean), 0, uniform_continuous(-10,10))
assume mean = if (is_funny) { funny_mean } else { 0 }
assume trial = proc() { normal(mean, 1) }
observe trial() = 8
observe trial() = 8
observe trial() = 8
observe trial() = 8
infer emap(default, all, 1, false)
""")
  eq_(True, r.sample("is_funny"))
  assert_almost_equal(8, r.sample("funny_mean"))

