import numpy as np
import numpy.linalg as la
import numpy.random as npr

def linear(x1, x2):
  return x1 * x2

def squared_exponential(a, l):
  def f(x1, x2):
    return a * np.exp(- la.norm((x1-x2)/l))
  return f

from venture import shortcuts as s
ripl = s.make_lite_church_prime_ripl()

from venture.lite.function import VentureFunction
from venture.lite.sp import SPType
import venture.lite.value as v
import venture.value.dicts as d

# input and output types for gp
xType = v.NumberType()
oType = v.NumberType()

ripl.assume('app', 'apply_function')

constantType = SPType([v.AnyType()], oType)
def makeConstFunc(c):
  return VentureFunction(lambda _: c, sp_type=constantType)

ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], constantType))

#ripl.assume('zero', "(app make_const_func 0)")
#print ripl.predict('(app zero 1)')

squaredExponentialType = SPType([xType, xType], oType)
def makeSquaredExponential(a, l):
  return VentureFunction(squared_exponential(a, l), sp_type=squaredExponentialType)

ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [v.NumberType(), xType], v.AnyType("VentureFunction")))

#ripl.assume('sq_exp', '(app make_squared_exponential 1 1)')
#print ripl.predict('(app sq_exp 0 1)')

program = """
  [assume mu (normal 0 5)]
;  [assume a (inv_gamma 2 5)]
  [assume a 1]
  [assume l (inv_gamma 5 100)]
;  [assume l (uniform_continuous 10 100)]
  
  [assume mean (app make_const_func mu)]
  [assume cov (app make_squared_exponential a l)]
  
  gp : [assume gp (make_gp mean cov)]
  
  [assume obs_fn (lambda (obs_id x) (gp x))]
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

