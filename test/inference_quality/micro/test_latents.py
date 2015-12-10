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

from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import skipWhenRejectionSampling
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

# TODO this is just one idea for how to encode matrices.
# Not sure what the interface to make_lazy_hmm should be.
# Note that different backends have used different conventions
# for row/column vectors, so I want to make that explicit.
@on_inf_prim("any")
@statisticalTest
def testHMMSP1():
  ripl = get_ripl()
  ripl.assume("f","""
(make_lazy_hmm
 (simplex 0.5 0.5)
 (matrix (array (array 0.7 0.3)
               (array 0.3 0.7)))
 (matrix (array (array 0.9 0.2)
               (array 0.1 0.8))))
""")
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)",label="pid")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,"pid")
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("any")
@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testHMMSP2():
  ripl = get_ripl()
  ripl.assume("f","""
(if (flip)
(make_lazy_hmm
 (simplex 0.5 0.5)
 (matrix (array (array 0.7 0.3)
               (array 0.3 0.7)))
 (matrix (array (array 0.9 0.2)
               (array 0.1 0.8))))
(make_lazy_hmm
 (simplex 0.5 0.5)
 (matrix (array (array 0.7 0.3)
               (array 0.3 0.7)))
 (matrix (array (array 0.9 0.2)
               (array 0.1 0.8)))))
""")
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)",label="pid")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,"pid")
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete(ans, predictions)
