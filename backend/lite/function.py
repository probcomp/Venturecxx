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
from venture.lite.utils import override
from venture.lite.value import VentureArray
from venture.lite.value import VentureValue
from venture.lite.value import registerVentureType
import venture.value.dicts as v

# This doesn't subclass VentureSPRecord, as if it did, then
# the trace would turn it into an SPRef. While this would make it
# a first-class function in Venture, it would prevent other SPs
# (like a GP) from using it as a function without requests.
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
  r"""Tangent vector to a point in a parametrized function space.

  Fix a parametric family of functions F_theta: X ---> Y for some
  theta = (theta^0, theta^1, ..., theta^{n-1}) in a linear parameter
  space Theta = Theta_0 x Theta_1 x ... x Theta_{n-1}, where for any
  fixed x_0 in X, the map

    theta |---> F_theta(x_0)

  is differentiable.

  This object contains a pair of Python functions (f, df), with an
  implicit fixed value of theta_0, so that for any x in X, f(x)
  computes F_{theta_0}(x), and df(x) computes an array of the partial
  derivatives of F_theta(x) with respect to theta^0, theta^1, ...,
  theta^{n-1}, at the point theta_0.

  Specifically, for x in X, f(x) = y is an element of Y, and df(x) =
  [t_0, t_1, ..., t_{n-1}] is an array of multipliers t_i to
  increments in theta^i giving increments in y, so that, in glib
  differential form,

    dy = t_0 dtheta^0 + t_1 dtheta^1 + ... + t_{n-1} dtheta^{n-1}.

  The parameter spaces Theta_i may be scalar or product spaces
  themselves.
  """

  def __init__(self, f, df, parameters, *args, **kwargs):
    super(VentureTangentFunction, self).__init__(f, *args, **kwargs)
    self._df = df
    self._parameters = parameters

  @property
  def df(self):
    return self._df
  @property
  def parameters(self):
    return self._parameters

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

class Param(object):
  def __init__(self):
    raise NotImplementedError
  def flat_size(self):
    raise NotImplementedError

class ParamLeaf(Param):
  @override(Param)
  def __init__(self):
    pass

  @override(Param)
  def flat_size(self):
    return 1

class ParamProduct(Param):
  @override(Param)
  def __init__(self, factors):
    assert isinstance(factors, list)
    self._factors = factors
    self._flat_size = sum(f.flat_size() for f in factors)

  @override(Param)
  def flat_size(self):
    return self._flat_size

  @property
  def factors(self):
    return self._factors

def parameter_nest(parameters, flat_args):
  args = []
  i = 0
  for p in parameters:
    s = p.flat_size()
    assert s <= len(flat_args)
    if isinstance(p, ParamLeaf):
      assert s == 1
      args += flat_args[i : i+s]
    else:
      args.append(VentureArray(flat_args[i : i+s]))
    i += s
  assert i == len(flat_args)
  return args

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
