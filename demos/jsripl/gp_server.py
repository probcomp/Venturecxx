# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

import numpy as np
import numpy.linalg as la
import numpy.random as npr

def linear(v, c):
  def f(x1, x2):
    return v * (x1-c) * (x2-c)
  return f

def squared_exponential(a, l):
  def f(x1, x2):
    x = (x1-x2)/l
    return a * np.exp(- np.dot(x, x))
  return f

def lift_binary(op):
  def lifted(f1, f2):
    return lambda *xs: op(f1(*xs), f2(*xs))
  return lifted

from venture import shortcuts as s
ripl = s.make_lite_church_prime_ripl()

from venture.lite.function import VentureFunction
from venture.lite.sp import SPType
import venture.lite.value as v
import venture.value.dicts as d

fType = v.AnyType("VentureFunction")

# input and output types for gp
xType = v.NumberType()
oType = v.NumberType()
kernelType = SPType([xType, xType], oType)

ripl.assume('app', 'apply_function')

constantType = SPType([v.AnyType()], oType)
def makeConstFunc(c):
  return VentureFunction(lambda _: c, sp_type=constantType)

ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], constantType))

#ripl.assume('zero', "(app make_const_func 0)")
#print ripl.predict('(app zero 1)')

def makeSquaredExponential(a, l):
  return VentureFunction(squared_exponential(a, l), sp_type=kernelType)

ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [v.NumberType(), xType], fType))

#ripl.assume('sq_exp', '(app make_squared_exponential 1 1)')
#print ripl.predict('(app sq_exp 0 1)')

def makeLinear(v, c):
  return VentureFunction(linear(v, c), sp_type=kernelType)

ripl.assume('make_linear', VentureFunction(makeLinear, [v.NumberType(), xType], fType))
#ripl.assume('linear', '(app make_linear 1 1)')
#print ripl.predict('(app linear 2 3)')

liftedBinaryType = SPType([v.AnyType(), v.AnyType()], v.AnyType())

def makeLiftedBinary(op):
  lifted_op = lift_binary(op)
  def wrapped(f1, f2):
    sp_type = f1.sp_type
    assert(f2.sp_type == sp_type)
    return VentureFunction(lifted_op(f1, f2), sp_type=sp_type)
  return VentureFunction(wrapped, sp_type=liftedBinaryType)

ripl.assume("func_plus", makeLiftedBinary(lambda x1, x2: x1+x2))
#print ripl.predict('(app (app func_plus sq_exp sq_exp) 0 1)')
ripl.assume("func_times", makeLiftedBinary(lambda x1, x2: x1*x2))

program = """
  [assume mu (normal 0 5)]
;  [assume a (inv_gamma 2 5)]
  [assume a 1]
  [assume l (inv_gamma 5 100)]
;  [assume l (uniform_continuous 10 100)]
  
  [assume mean (app make_const_func mu)]
  [assume cov (app make_squared_exponential a l)]
;  [assume cov (app make_linear a 0)]
  
  gp : [assume gp (make_gp mean cov)]
  
  [assume obs_fn (lambda (obs_id x) (gp x))]
;  [assume obs_fn (lambda (obs_id x) (normal x 1))]
"""

ripl.execute_program(program)

samples = [
  (0, 1),
  (2, 3),
  (-4, 5),
]

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), xType)

xs, os = zip(*samples)

#ripl.observe(['gp', array(xs)], array(os))
ripl.infer("(incorporate)")

from venture.server import RiplRestServer

server = RiplRestServer(ripl)
server.run(host='0.0.0.0', port=8082)

