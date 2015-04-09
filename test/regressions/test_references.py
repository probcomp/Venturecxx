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

from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testReferences1():
  """Checks that the program runs without crashing. At some point, this
program caused the old CXX backend to fire an assert.  When the (flip)
had a 0.0 or 1.0 it didn't fail."""
  ripl = get_ripl()
  ripl.assume("draw_type0", "(make_crp 1.0)")
  ripl.assume("draw_type1", "(if (flip) draw_type0 (lambda () atom<1>))")
  ripl.assume("draw_type2", "(make_dir_mult (array 1.0 1.0))")
  ripl.assume("class", "(if (flip) (lambda (name) (draw_type1)) (lambda (name) (draw_type2)))")
  ripl.predict("(class 1)")
  ripl.predict("(flip)", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete(ans, predictions)


@statisticalTest
def testReferences2():
  "Simpler version of the old bug testReferences1() tries to trigger"
  ripl = get_ripl()
  ripl.assume("f", "(if (flip 0.5) (make_dir_mult (array 1.0 1.0)) (lambda () atom<1>))")
  ripl.predict("(f)", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete(ans, predictions)
