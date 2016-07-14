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

from nose.tools import assert_equal, assert_not_equal, make_decorator
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
            (let s nil)
            (extract s)
            (regen s)
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
            (let s nil)
            (weight_and_fragment <- (extract s))
            (restore s (rest weight_and_fragment))
            (z_ <- (predict (* x y)))
            (return (list z z_)))
        (%s))
""" % trace)
  rho_z, xi_z = result
  assert_equal(rho_z, xi_z)
