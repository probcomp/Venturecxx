# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples, on_inf_prim
import scipy.stats as stats
import venture.value.dicts as v

# TODO
# This file contains one possibility for the Dictionary interface
# Note that "lookup" would be shared by arrays and "contains" would be 
# shared by sets. Also note the convention of using the data-structure name
# (i.e. "dict") as the constructor.
# I probably prefer (dict (array k1 v1) ... (array kN vN))
# but will leave it as is for now. It would not be hard to check the argument types
# and allow either.

@on_inf_prim("none")
def testDict0():
  assert get_ripl().predict("(is_dict (dict (array) (array)))")

@on_inf_prim("none")
def testDict01():
  assert get_ripl().predict("(is_dict (dict (array 1) (array 2)))")

@on_inf_prim("none")
def testDictSize0():
  assert get_ripl().predict("(size (dict (array) (array)))") == 0

@on_inf_prim("none")
def testDictSize1():
  assert get_ripl().predict("(size (dict (array 1) (array 2)))") == 1

@on_inf_prim("none")
def testDictSize2():
  assert get_ripl().predict("(size (dict (array 1 5) (array 2 6)))") == 2

@statisticalTest
def testDict1():
  ripl = get_ripl()

  ripl.assume("x","(bernoulli 1.0)")
  ripl.assume("d","""(dict (array (quote x) (quote y))
                           (array (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("""(normal (+
                           (lookup d (quote x))
                           (lookup d (quote y))
                           (lookup d (quote y)))
                         1.0)""", label="pid")

  predictions = collectSamples(ripl,"pid")
  cdf = stats.norm(loc=20, scale=2).cdf
  return reportKnownContinuous(cdf, predictions, "N(20,2)")

@on_inf_prim("none")
def testDict2():
  ripl = get_ripl()
  ripl.assume("d","""(dict (array (quote x) (quote y))
                           (array (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(contains d (quote x))",label="p1")
  ripl.predict("(contains d (quote y))",label="p2")
  ripl.predict("(contains d (quote z))",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")

@on_inf_prim("none")
def testDict3():
  ripl = get_ripl()
  ripl.assume("d","""(dict (array atom<1> atom<2>)
                           (array (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(contains d atom<1>)",label="p1")
  ripl.predict("(contains d atom<2>)",label="p2")
  ripl.predict("(contains d atom<3>)",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")

@on_inf_prim("none")
def testStack():
  ripl = get_ripl()
  val = ripl.sample("(dict (array 1) (array 4))")
  assert val == ripl.sample(v.dict(val))
  
