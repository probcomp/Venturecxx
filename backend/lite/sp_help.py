# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

"""Helpers for creating SP objects."""

from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.psp import DeterministicPSP
from venture.lite.psp import DispatchingPSP
from venture.lite.psp import ESRRefOutputPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp import SP
from venture.lite.sp import SPType
import venture.lite.types as t

def no_request(output): return SP(NullRequestPSP(), output)

def esr_output(request): return SP(request, ESRRefOutputPSP())

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(output, SPType(args_types, return_type, **kwargs)))

class FunctionPSP(DeterministicPSP):
  def __init__(self, f, descr=None, sim_grad=None):
    self.f = f
    self.descr = descr
    self.sim_grad = sim_grad
    if self.descr is None:
      self.descr = "deterministic %s"
  def simulate(self,args):
    return self.f(args)
  def gradientOfSimulate(self, args, _value, direction):
    # Don't need the value if the function is deterministic, because
    # it consumes no randomness.
    if self.sim_grad:
      return self.sim_grad(args, direction)
    else:
      raise VentureBuiltinSPMethodError("Cannot compute simulation gradient of '%s'" % self.description("<unknown name>"))
  def description(self,name):
    if '%s' in self.descr:
      return self.descr % name
    else:
      return self.descr

def typed_func_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(FunctionPSP(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def typed_func(*args, **kwargs):
  return no_request(typed_func_psp(*args, **kwargs))

# TODO This should actually be named to distinguish it from the
# previous version, which accepts the whole args object (where this
# one splats the operand values).
def deterministic_psp(f, descr=None, sim_grad=None):
  def new_grad(args, direction):
    return sim_grad(args.operandValues(), direction)
  return FunctionPSP(lambda args: f(*args.operandValues()), descr, sim_grad=(new_grad if sim_grad else None))

def deterministic_typed_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(deterministic_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def deterministic(f, descr=None, sim_grad=None):
  return no_request(deterministic_psp(f, descr, sim_grad))

def deterministic_typed(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr, sim_grad), args_types, return_type, **kwargs)

def binaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType(), t.NumberType()], t.NumberType(), sim_grad=sim_grad, descr=descr)

def binaryNumS(output):
  return typed_nr(output, [t.NumberType(), t.NumberType()], t.NumberType())

def unaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType()], t.NumberType(), sim_grad=sim_grad, descr=descr)

def unaryNumS(f):
  return typed_nr(f, [t.NumberType()], t.NumberType())

def naryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType()], t.NumberType(), variadic=True, sim_grad=sim_grad, descr=descr)

def zero_gradient(args, _direction):
  return [0 for _ in args]

def binaryPred(f, descr=None):
  return deterministic_typed(f, [t.AnyType(), t.AnyType()], t.BoolType(), sim_grad=zero_gradient, descr=descr)

def type_test(tp):
  return deterministic_typed(lambda thing: thing in tp, [t.AnyType()], t.BoolType(),
                             sim_grad = zero_gradient,
                             descr="%s returns true iff its argument is a " + tp.name())

def dispatching_psp(types, psps):
  return DispatchingPSP(types, [TypedPSP(psp, tp) for (psp, tp) in zip(psps, types)])
