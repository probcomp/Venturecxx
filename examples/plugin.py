# A custom inference SP to make Vikash happy

import venture.lite.psp as psp
import venture.lite.value as v
from venture.lite.builtin import typed_nr

class MyInferencePSP(psp.RandomPSP):
  "In the inference language, this will be usable as a raw symbol (no parameters)"
  def __init__(self): pass
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    inferrer = args.operandValues[0]
    print 9
    return inferrer

my_sp = typed_nr(MyInferencePSP(), [v.ForeignBlobType()], v.ForeignBlobType())

# Install me at the Venture prompt with
#   eval execfile("examples/plugin.py"); self.ripl.bind_foreign_inference_sp("foo", my_sp)
# Then enjoy with
#   infer (cycle (foo) 10)
