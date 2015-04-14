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

def assertTorus(scaffold):
  for _,regenCount in scaffold.regenCounts.iteritems(): 
    assert regenCount == 0

def assertTrace(trace,scaffold):
  for node in scaffold.regenCounts:
    assert trace.valueAt(node) is not None

def assertSameScaffolds(scaffoldA,scaffoldB):
  assert len(scaffoldA.regenCounts) == len(scaffoldB.regenCounts)
  assert len(scaffoldA.absorbing) == len(scaffoldB.absorbing)
  assert len(scaffoldA.aaa) == len(scaffoldB.aaa)
  assert len(scaffoldA.border) == len(scaffoldB.border)
  for node in scaffoldA.regenCounts:
    assert scaffoldA.getRegenCount(node) == scaffoldB.getRegenCount(node)

