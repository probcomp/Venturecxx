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
import random

import libpumatrace as puma

from venture.lite.sp import VentureSPRecord
from venture.lite.value import VentureValue
from venture.lite.builtin import builtInSPs
import venture.lite.foreign as foreign
import venture.value.dicts as v

class WarningPSP(object):
  warned = {}
  def __init__(self, name, psp):
    self.name = name
    self.psp = psp

  def __getattr__(self, attrname):
    sub = getattr(self.psp, attrname)
    def f(*args, **kwargs):
      if not self.name in WarningPSP.warned:
        print "Warning: Defaulting to using %s from Python, likely to be slow" % self.name
        WarningPSP.warned[self.name] = True
      return sub(*args, **kwargs)
    return f

class WarningSP(object):
  def __init__(self, name, sp):
    self.requestPSP = WarningPSP(name, sp.requestPSP)
    self.outputPSP = WarningPSP(name, sp.outputPSP)
    self.sp = sp

  def __getattr__(self, attrname):
    return getattr(self.sp, attrname)

class Trace(object):
  def __init__(self, trace=None):
    if trace is None:
      self.trace = puma.Trace()
      # Poor Puma defaults its local RNG seed to the system time
      self.trace.set_seed(random.randint(1,2**31-1))
      for name,sp in builtInSPs().iteritems():
        if self.trace.boundInGlobalEnv(name):
          # Already there
          pass
        else:
          # Use the Python SP as a fallback to not having a fast one
          self.bindPrimitiveSP(name, WarningSP(name, sp))
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
    if isinstance(sp, puma.PumaSP):
      self.trace.bindPumaSP(name, sp)
    else:
      self.trace.bindPythonSP(name, foreign.ForeignLiteSP(sp))

  def extractValue(self, did):
    ret = self.trace.extractValue(did)
    if ret["type"] == "foreign_sp":
      ret = VentureSPRecord(ret["sp"], ret["aux"]).asStackDict(None)
    return ret

  def primitive_infer(self, exp):
    self.trace.primitive_infer(_expToDict(exp))

  def log_likelihood_at(self, scope, block):
    return self.trace.log_likelihood_at(_ensure_stack_dict(scope),
                                        _ensure_stack_dict(block))

  def log_joint_at(self, scope, block):
    return self.trace.log_joint_at(_ensure_stack_dict(scope),
                                   _ensure_stack_dict(block))

  def numNodesInBlock(self, scope, block):
    # This is kooky for compatibility with the Lite numNodesInBlock method.
    def guess_type(obj):
      if isinstance(obj, int):
        return v.number(obj)
      if isinstance(obj, basestring):
        return v.symbol(obj)
      raise Exception("numNodesInBlock can't handle %s" % obj)
    return self.trace.numNodesInBlock(guess_type(scope), guess_type(block))

  def set_profiling(self, _enabled):
    pass # Puma can't be internally profiled (currently)

  def clear_profiling(self): pass

def _unwrapVentureValue(val):
  if isinstance(val, VentureValue):
    return val.asStackDict(None)["value"]
  return val

def _ensure_stack_dict(val):
  assert isinstance(val, VentureValue)
  return val.asStackDict(None)

def _expToDict(exp):
  print exp
  if isinstance(exp, int):
    return {"kernel":"mh", "scope":"default", "block":"one", "transitions": exp}

  scope = _ensure_stack_dict(exp[1])
  block = _ensure_stack_dict(exp[2])

  exp = map(_unwrapVentureValue, exp)

  tag = exp[0]
  if tag == "mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":scope,"block":block,"transitions":int(exp[3])}
  elif tag == "bogo_possibilize":
    assert len(exp) == 4
    return {"kernel":"bogo_possibilize","scope":scope,"block":block,"transitions":int(exp[3])}
  elif tag == "func_mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":scope,"block":block,"transitions":int(exp[3])}
  elif tag == "gibbs":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"gibbs","scope":scope,"block":block,"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "emap":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"emap","scope":scope,"block":block,"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "slice":
    assert len(exp) == 6
    return {"kernel":"slice","scope":scope,"block":block,"w":exp[3],"m":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "slice_doubling":
    assert len(exp) == 6
    return {"kernel":"slice_doubling","scope":scope,"block":block,"w":exp[3],"p":int(exp[4]),"transitions":int(exp[5])}
  # [FIXME] expedient hack for now to allow windowing with pgibbs.
  elif tag == "pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    if type(block["value"]) is list:
      range_spec = block["value"]
      assert range_spec[0]["value"] == "ordered_range"
      ans = {"kernel":"pgibbs","scope":scope,"block":v.symbol("ordered_range"),
            "min_block":range_spec[1],"max_block":range_spec[2],
            "particles":int(exp[3]),"transitions":int(exp[4])}
    else:
      ans = {"kernel":"pgibbs","scope":scope,"block":block,"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "func_pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    ans = {"kernel":"pgibbs","scope":scope,"block":block,"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    else:
      ans["in_parallel"] = True
    return ans
  elif tag == "meanfield":
    assert len(exp) == 5
    return {"kernel":"meanfield","scope":scope,"block":block,"steps":int(exp[3]),"transitions":int(exp[4])}
  elif tag == "hmc":
    assert len(exp) == 6
    return {"kernel":"hmc","scope":scope,"block":block,"epsilon":exp[3],"L":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "map":
    assert len(exp) == 6
    return {"kernel":"map","scope":scope,"block":block,"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "nesterov":
    assert len(exp) == 6
    return {"kernel":"nesterov","scope":scope,"block":block,"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "latents":
    assert len(exp) == 4
    return {"kernel":"latents","scope":scope,"block":block,"transitions":int(exp[3])}
  elif tag == "rejection":
    assert len(exp) >= 3
    assert len(exp) <= 4
    if len(exp) == 4:
      return {"kernel":"rejection","scope":scope,"block":block,"transitions":int(exp[3])}
    else:
      return {"kernel":"rejection","scope":scope,"block":block,"transitions":1}
  else:
    raise Exception("Cannot parse infer instruction")
