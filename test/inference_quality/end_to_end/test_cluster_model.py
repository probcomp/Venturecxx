# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

from nose.plugins.attrib import attr
from nose.tools import assert_less, assert_greater

from venture.test.config import get_ripl, on_inf_prim

def mean(xs): return sum(xs) / float(len(xs))

@attr("slow")    
@on_inf_prim("mh")
def testCRPMixSimple1():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.predict("(get_cluster_mean 1)",label="cmean")
  
  ripl.observe("(normal (get_cluster_mean 1) 1)","5")

  B = 50
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)

