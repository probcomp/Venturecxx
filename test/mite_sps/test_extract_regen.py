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

import scipy

from nose.tools import assert_equal, assert_not_equal, assert_almost_equal
from nose.tools import make_decorator
from nose import SkipTest

from venture.test.config import get_ripl
from venture.test.config import gen_on_inf_prim

def gen_for_each(items):
  def wrap(f):
    @make_decorator(f)
    def wrapped():
      for item in items:
        yield f, item
    return wrapped
  return wrap

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testExtractRegen(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (z <- (predict (* x y)))
            (s <- (select nil))
            (weight_and_fragment <- (extract s))
            (regen s (rest weight_and_fragment))
            (z_ <- (predict (* x y)))
            (return (list z z_)))
        (%s))
""" % trace)
  rho_z, xi_z = result
  assert_not_equal(rho_z, xi_z)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testExtractRestore(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (z <- (predict (* x y)))
            (s <- (select nil))
            (weight_and_fragment <- (extract s))
            (restore s (rest weight_and_fragment))
            (z_ <- (predict (* x y)))
            (return (list z z_)))
        (%s))
""" % trace)
  rho_z, xi_z = result
  assert_equal(rho_z, xi_z)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testExtractRegenLambda(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (assume f (lambda (x y) (+ x y 1)))
            (z <- (predict (f x y)))
            (s <- (select nil))
            (weight_and_fragment <- (extract s))
            (regen s (rest weight_and_fragment))
            (z_ <- (predict (f x y)))
            (return (list z z_)))
        (%s))
""" % trace)
  rho_z, xi_z = result
  assert_not_equal(rho_z, xi_z)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testExtractRestoreLambda(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (assume f (lambda (x y) (+ x y 1)))
            (z <- (predict (f x y)))
            (s <- (select nil))
            (weight_and_fragment <- (extract s))
            (restore s (rest weight_and_fragment))
            (z_ <- (predict (f x y)))
            (return (list z z_)))
        (%s))
""" % trace)
  rho_z, xi_z = result
  assert_equal(rho_z, xi_z)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testSelectRegen1(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (x <- (predict x))
            (y <- (predict y))
            (s <- (pyselect "{
                     directive(2): {'type': 'proposal'},
                   }"))
            (weight_and_fragment <- (extract s))
            (regen s (rest weight_and_fragment))
            (x_ <- (predict x))
            (y_ <- (predict y))
            (return (list x x_ y y_)))
        (%s))
""" % trace)
  (x, x_, y, y_) = result
  assert_equal(x, x_)
  assert_not_equal(y, y_)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testSelectRegen2(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (x <- (predict x))
            (y <- (predict y))
            (s <- (pyselect "{
                     directive(1): {'type': 'proposal'},
                     directive(2): {'type': 'proposal'},
                   }"))
            (weight_and_fragment <- (extract s))
            (regen s (rest weight_and_fragment))
            (x_ <- (predict x))
            (y_ <- (predict y))
            (return (list x x_ y y_)))
        (%s))
""" % trace)
  (x, x_, y, y_) = result
  assert_not_equal(x, x_)
  assert_not_equal(y, y_)

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testSelectRegen3(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (x <- (predict x))
            (y <- (predict y))
            (s <- (pyselectf "{
                     directive(2): {'type': 'constrained',
                                    'val': y}
                   }" (dict (list 'y) (list 4))))
            (weight_and_fragment <- (extract s))
            (weight <- (regen s (rest weight_and_fragment)))
            (x_ <- (predict x))
            (y_ <- (predict y))
            (return (list x x_ y y_ weight)))
        (%s))
""" % trace)
  (x, x_, y, y_, weight) = result
  assert_equal(x, x_)
  assert_equal(y_, 4)
  assert_almost_equal(weight, scipy.stats.norm(x_, 1).logpdf(y_))

@gen_on_inf_prim("none")
@gen_for_each(["flat_trace", "graph_trace"])
def testSelectRegen4(trace):
  if trace == "graph_trace":
    raise SkipTest("regen not yet implemented for graph trace")
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x (normal 0 1))
            (assume y (normal x 1))
            (x <- (predict x))
            (y <- (predict y))
            (s <- (pyselectf "{
                     directive(1): {'type': 'proposal'},
                     directive(2): {'type': 'constrained',
                                    'val': y},
                   }" (dict (list 'y) (list y))))
            (weight_and_fragment <- (extract s))
            (weight <- (regen s (rest weight_and_fragment)))
            (x_ <- (predict x))
            (y_ <- (predict y))
            (return (list x x_ y y_ weight)))
        (%s))
""" % trace)
  (x, x_, y, y_, weight) = result
  assert_not_equal(x, x_)
  assert_equal(y, y_)
  assert_almost_equal(weight, scipy.stats.norm(x_, 1).logpdf(y_))
