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

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import SP
from venture.lite.sp import SPType
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.value import VentureValue
from venture.lite.value import registerVentureType
import venture.value.dicts as v

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

class VentureTangentFunction(VentureFunction):
  """Tangent vector to a point in a finitely parametrized function space.

  A tangent vector is a pair (f, df) where f is a function and df
  represents a direction in the function space by a function of the
  same arguments that returns a list of partial derivatives, one for
  each parameter in the space.

  Specifically, if for any theta = (theta_0, theta_1, ...,
  theta_{k-1}) in a parameter space Theta, there is a function
  F_theta: X ---> Y, such that for fixed x_0, the map

        theta |---> F_theta(x_0)

  is differentiable, a VentureTangentFunction object represents a
  tuple (f, df) = (F_theta, d/dtheta F_theta), in the sense that for
  any x, f(x) computes F_theta(x), and df(x) computes a list of k
  partial derivatives [d/dtheta_0 F_theta(x), d/dtheta_1 F_theta(x),
  ..., d/dtheta_{k-1} F_theta(x)] in all parameter directions.
  """

  def __init__(self, f, df, *args, **kwargs):
    super(VentureTangentFunction, self).__init__(f, *args, **kwargs)
    self.df = df

  def gradient_type(self):
    return VentureTangentFunction

  @staticmethod
  def fromStackDict(thing):
    derivative = thing.pop('derivative')
    return VentureTangentFunction(thing['value'], derivative, **thing)

  def asStackDict(self, _trace=None):
    val = v.val('diffable_function', self.f)
    val['derivative'] = self.df
    val['sp_type'] = self.sp_type
    val.update(self.stuff)
    return val

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
