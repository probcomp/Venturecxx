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

from itertools import chain
import numpy.random as npr

class Node(object):
  """Binary tree to speed up categorical sampling."""
  def __init__(self, vals):
    if len(vals) == 0:
      raise ValueError("Can't instantiate Node with empty values.")

    self.leaf = len(vals) == 1

    if self.leaf:
      self.total = vals[0]
    else:
      self.mid = len(vals) // 2
      self.left = Node(vals[:self.mid])
      self.right = Node(vals[self.mid:])
      self.total = self.left.total + self.right.total

  def __getitem__(self, index):
    if self.leaf:
      return self.total
    elif index < self.mid:
      return self.left[index]
    else:
      return self.right[index - self.mid]

  def delta(self, index, d):
    self.total += d
    if not self.leaf:
      if index < self.mid:
        self.left.delta(index, d)
      else:
        self.right.delta(index - self.mid, d)

  def increment(self, index):
    self.delta(index, 1)

  def decrement(self, index):
    self.delta(index, -1)

  def __setitem__(self, index, value):
    self.delta(index, value - self[index])

  def __iter__(self):
    if self.leaf:
      yield self.total
    else:
      for leaf in chain(self.left, self.right):
        yield leaf

  def leaves(self):
    return list(self)

  def __len__(self):
    if self.leaf:
      return 1
    else:
      return len(self.left) + len(self.right)

def sample(*nodes):
  n = nodes[0]

  if n.leaf: return 0

  total = sum(node.total for node in nodes)
  left = sum(node.left.total for node in nodes)

  if npr.random() * total < left:
    return sample(*[node.left for node in nodes])
  else:
    return n.mid + sample(*[node.right for node in nodes])

