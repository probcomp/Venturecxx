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

import random

class SamplableMap(object):
  def __init__(self):
    self.d = {}
    self.a = []

  def __getitem__(self,k):
    return self.a[self.d[k]][1]


  def __setitem__(self,k,v):
    assert not k in self.d
    self.d[k] = len(self.a)
    self.a.append((k,v))

  def __delitem__(self,k):
    assert k in self.d
    index = self.d[k]
    lastIndex = len(self.a) - 1
    lastPair = self.a[lastIndex]

    self.d[lastPair[0]] = index
    self.a[index] = lastPair

    self.a.pop()
    del self.d[k]
    assert len(self.d) == len(self.a)

  def __contains__(self,k): return k in self.d
  def __len__(self): return len(self.a)

  def __str__(self): return "SamplableMap: " + self._as_dict().__str__()
  def __repr__(self): return "SamplableMap: " + self._as_dict().__repr__()

  def _as_dict(self):
    return {k:self[k] for k in self.d}

  def sample(self): return random.sample(self.a,1)[0]

  def keys(self): return self.d.keys()

  def values(self): return [v for (_,v) in self.a]
