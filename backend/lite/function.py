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

from value import VentureValue, registerVentureType
from psp import DeterministicPSP, NullRequestPSP
from sp import SP, SPType
import venture.value.dicts as v

from sp_registry import registerBuiltinSP

"""This doesn't subclass VentureSPRecord, as if it did, then
the trace would turn it into an SPRef. While this would make it
a first-class function in Venture, it would prevent other SPs
(like a GP) from using it as a function without requests."""
class VentureFunction(VentureValue):
  def __init__(self, f, args_types=None, return_type=None, sp_type=None, **kwargs):
    if sp_type is not None:
      args_types = sp_type.args_types
      return_type = sp_type.return_type
    else:
      sp_type = SPType(args_types, return_type)

    self.f = f
    self.sp_type = sp_type
    self.stuff = kwargs
  
  @staticmethod
  def fromStackDict(thing):
    return VentureFunction(thing['value'], **thing)
  
  def asStackDict(self, _trace=None):
    val = v.val("function", self.f)
    val["sp_type"] = self.sp_type
    val.update(self.stuff)
    return val
  
  def __call__(self, *args):
    return self.f(*args)

registerVentureType(VentureFunction, "function")

class ApplyFunctionOutputPSP(DeterministicPSP):
  def simulate(self,args):
    vals = args.operandValues()
    function = vals[0]
    arguments = vals[1:]
    
    sp_type = function.sp_type
    unwrapped_args = sp_type.unwrap_arg_list(arguments)
    #print sp_type.name(), unwrapped_args
    
    returned = function.f(*unwrapped_args)
    wrapped_return = sp_type.wrap_return(returned)
    
    return wrapped_return
  
  def description(self,_name=None):
    return "Apply a VentureFunction to arguments."

# TODO Add type signature. Look at signature of apply?
applyFunctionSP = SP(NullRequestPSP(), ApplyFunctionOutputPSP())

registerBuiltinSP("apply_function", applyFunctionSP)
