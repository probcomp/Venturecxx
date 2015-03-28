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
import random

import libpumatrace as puma

from venture.lite.value import VentureValue
import venture.lite.foreign as foreign

class Trace(object):
  def __init__(self, trace=None):
    if trace is None:
      self.trace = puma.Trace()
      # Poor Puma defaults its local RNG seed to the system time
      self.trace.set_seed(random.randint(1,2**31-1))
    else:
      assert isinstance(trace, puma.Trace)
      self.trace = trace

  def __getattr__(self, attrname):
    # Forward all other trace methods without modification
    return getattr(self.trace, attrname)

  def has_own_prng(self): return True

  def stop_and_copy(self):
    return Trace(self.trace.stop_and_copy())

  def short_circuit_copyable(self): return True

  # Not intercepting the "diversify" method because Puma doesn't
  # support it.  If Puma does come to support it, will need to wrap it
  # here to drop the copy_trace argument (because presumably Puma will
  # have no need of that, using stop_and_copy instead).

  def bindPrimitiveSP(self, name, sp):
    self.trace.bindPrimitiveSP(name, foreign.ForeignLiteSP(sp))

  def primitive_infer(self, exp):
    self.trace.primitive_infer(_expToDict(exp))

  def set_profiling(self, _enabled): pass # Puma can't be internally profiled (currently)
  def clear_profiling(self): pass

def _unwrapVentureValue(val):
  if isinstance(val, VentureValue):
    return val.asStackDict(None)["value"]
  return val

def _expToDict(exp):
  if isinstance(exp, int):
    return {"kernel":"mh", "scope":"default", "block":"one", "transitions": exp}

  exp = map(_unwrapVentureValue, exp)

  tag = exp[0]
  if tag == "mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "bogo_possibilize":
    assert len(exp) == 4
    return {"kernel":"bogo_possibilize","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "func_mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "gibbs":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"gibbs","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "emap":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"emap","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "slice":
    assert len(exp) == 6
    return {"kernel":"slice","scope":exp[1],"block":exp[2],"w":exp[3],"m":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "slice_doubling":
    assert len(exp) == 6
    return {"kernel":"slice_doubling","scope":exp[1],"block":exp[2],"w":exp[3],"p":int(exp[4]),"transitions":int(exp[5])}
  # [FIXME] expedient hack for now to allow windowing with pgibbs.
  elif tag == "pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    if type(exp[2]) is list:
      range_spec = [d["value"] for d in exp[2]]
      assert range_spec[0] == "ordered_range"
      ans = {"kernel":"pgibbs","scope":exp[1],"block":"ordered_range",
            "min_block":range_spec[1],"max_block":range_spec[2],
            "particles":int(exp[3]),"transitions":int(exp[4])}
    else:
      ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "func_pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "meanfield":
    assert len(exp) == 5
    return {"kernel":"meanfield","scope":exp[1],"block":exp[2],"steps":int(exp[3]),"transitions":int(exp[4])}
  elif tag == "hmc":
    assert len(exp) == 6
    return {"kernel":"hmc","scope":exp[1],"block":exp[2],"epsilon":exp[3],"L":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "map":
    assert len(exp) == 6
    return {"kernel":"map","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "nesterov":
    assert len(exp) == 6
    return {"kernel":"nesterov","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "latents":
    assert len(exp) == 4
    return {"kernel":"latents","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "rejection":
    assert len(exp) >= 3
    assert len(exp) <= 4
    if len(exp) == 4:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    else:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":1}
  else:
    raise Exception("Cannot parse infer instruction")
