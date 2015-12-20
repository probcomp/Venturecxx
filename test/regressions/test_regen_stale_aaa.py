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

from venture.test.config import get_ripl

def testRegenStaleAAA():
  """
  This test ensures that if an AAA procedure is being resampled in the
  same scaffold as something that reads it through an SPRef, the AAA
  procedure gets regenerated not later than the thing that reads it.
  """
  # TODO: The regen order depends on how the border nodes are sorted,
  # which is (I think) unspecified, so this test might not necessarily
  # fail even without the stale AAA check. Is there a way to exercise
  # all possible regen orders of this program?
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_beta_bernoulli a a)")
  ripl.predict("(f)")
  ripl.infer("(mh default all 1)")
