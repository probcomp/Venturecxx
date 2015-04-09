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

"""The goal of this module is to abstract robustly storing numpy-able
data in numpy arrays, storing non-numpy-able data in plain Python
lists, and avoiding copying either if it is not necessary.  Also, when
operations on the data are called for, applying numpy operations if
possible.

"""

def ensure_numpy_if_possible(_elt_type, data):
  return data

def map(f, data, _elt_type):
  """Assume that the function preserves the element type."""
  return [f(d) for d in data]

def map2(f, data1, elt_type1, data2, elt_type2):
  """For situations that would convert one or another element type (e.g., automatic promotions), map2 returns the
resulting data and its element type in a tuple."""
  assert elt_type1 == elt_type2
  return [f(d1, d2) for (d1, d2) in zip(data1, data2)], elt_type1

def dot(data1, _elt_type1, data2, _elt_type2):
  return sum([x * y for (x,y) in zip(data1, data2)])
