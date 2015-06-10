# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from ..lite import value as vv
from ..lite import types as t

def normalize(value):
  if value is None:
    return None
  elif isinstance(value, vv.VentureValue):
    # Possible for programmatic construction, e.g. builtin.py
    # Will also occur for literal atoms, since there's no other way
    # to tell them apart from literal numbers.
    return value
  else: # In eval
    return t.ExpressionType().asVentureValue(value)

class Node(object):
  def __init__(self, address, value = None):
    self.address = address
    self.value = normalize(value)
