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

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("resample") # And MH, but it's testing resample more
def testUnevalConstantAndForget():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  ripl = get_ripl()
  ripl.predict("(if (flip) 0 1)", label="pid")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.forget("pid")
  ripl.infer("(resample 5)")

@on_inf_prim("resample") # And MH, but it's testing resample more
def testUnevalConstantAndFreeze():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)", label="pid")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.freeze("pid")
  ripl.infer("(resample 5)")

@on_inf_prim("resample") # And MH, but it's testing resample more
def testUnevalConstantAndFreezeWithObservations():
  """Check that unevaling a constant node does not produce an invalid
trace (even when transitions are rejected)."""
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)", label="pid")
  ripl.observe("(normal foo 0.1)", 1)
  ripl.infer(40)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.freeze("pid")
  ripl.infer("(resample 5)")
