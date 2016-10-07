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

class VenturePartialDiffableFunction(VentureFunction):
  r"""Differentiable function family closed over differentiable parameters.

  Fix a parametric family of functions F_theta: X x Y ---> Z for some
  theta = (theta^0, theta^1, ..., theta^{n-1}) in a parameter space
  Theta = Theta_0 x Theta_1 x ... x Theta_{n-1}, where for any fixed
  x_0 in X and y_0 in Y, the map

    theta |---> F_theta(x_0, y_0),

  is differentiable, and for any fixed theta_0 in Theta and y_0 in Y,
  the map

    x |---> F_{theta_0}(x, y_0)

  is differentiable.

  This object contains a triple of Python functions (f, g, h) closed
  over an implicit fixed value of theta_0, so that for any x in X and
  y in Y,

    f(x, y) computes F_{theta_0}(x, y);
    g(x, y) computes F_{theta_0}(x, y) and the array of partial
      derivatives d/dtheta^i F_{theta_0}(x, y); and
    h(x, y) computes F_{theta_0}(x, y) and the partial derivative
      d/dx F_{theta_0}(x, y).

  Specifically, for x in X and y in Y,

    f(x, y) = z is an element of Z;
    g(x, y) = (z, [t_0, t_1, ..., t_{n-1}]) gives z and an array of
      multipliers t_i to increments in theta^i giving increments in z; and
    h(x, y) = (z, u) gives z and a multiplier to an increment in x giving
      an increment in z.

  In glib differential form,

    dz = t_0 dtheta^0 + t_1 dtheta^1 + ... + t_{n-1} dtheta^{n-1} + u dx.

  The parameter spaces Theta_i and X may be scalar or product spaces
  themselves.
  """

  def __init__(self, f, df_theta, df_x, parameters, *args, **kwargs):
    super(VenturePartialDiffableFunction, self).__init__(f, *args, **kwargs)
    self._df_theta = df_theta
    self._df_x = df_x
    self._parameters = parameters

  @property
  def df_theta(self):
    return self._df_theta
  @property
  def df_x(self):
    return self._df_x
  @property
  def parameters(self):
    return self._parameters

  @staticmethod
  def fromStackDict(thing):
    df_theta = thing.pop('parameter_derivative')
    df_x = thing.pop('partial_derivative')
    return VenturePartialDiffableFunction(thing['value'], df_theta, df_x,
      **thing)

  def asStackDict(self, _trace=None):
    val = v.val('diffable_function', self.f)
    val['parameter_derivative'] = self.df_theta
    val['partial_derivative'] = self.df_x
    val['sp_type'] = self.sp_type
    val.update(self.stuff)
    return val

class Param(object):
  def __init__(self):
    raise NotImplementedError
  def flat_size(self):
    raise NotImplementedError
  def __repr__(self):
    raise NotImplementedError

class ParamLeaf(Param):
  @override(Param)
  def __init__(self):
    pass

  @override(Param)
  def flat_size(self):
    return 1

  @override(Param)
  def __repr__(self):
    return 'R'

class ParamProduct(Param):
  @override(Param)
  def __init__(self, factors):
    assert isinstance(factors, list)
    self._factors = factors
    self._flat_size = sum(f.flat_size() for f in factors)

  @override(Param)
  def flat_size(self):
    return self._flat_size

  @override(Param)
  def __repr__(self):
    return 'P(%s)' % (','.join(f.__repr__() for f in self.factors),)

  @property
  def factors(self):
    return self._factors

def parameter_nest(parameters, flat_args):
  """Apply one level of nested parametrization to a flat array.

  A tree of real parameters, e.g. (R^3 x R^2) x R x R^4, may be
  flattened by the natural isomorphism to R^10.  Given the shape (R^3
  x R^2) x R x R^4 and an element of R^7, this function undoes one
  level of that tree, yielding an element of R^5 x R x R^4.

  The caller can then apply it again to the shape R^3 x R^2 and the
  resulting element of R^5 to get an element of R^3 x R^2, and thereby
  recover an element of the completely nested (R^3 x R^2) x R x R^4.
  """
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
