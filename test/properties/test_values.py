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

# Invariants that should hold about VentureValue objects

from venture.test.config import in_backend
from venture.test.randomized import checkTypedProperty
import venture.lite.value as vv
from venture.parser.church_prime import ChurchPrimeParser

@in_backend("none")
def testEquality():
  checkTypedProperty(propEquality, vv.AnyType())

def propEquality(value):
  assert value.equal(value)

@in_backend("none")
def testLiteToStack():
  checkTypedProperty(propLiteToStack, vv.AnyType())

def propLiteToStack(val):
  assert val.equal(vv.VentureValue.fromStackDict(val.asStackDict()))

@in_backend("none")
def testLiteToString():
  checkTypedProperty(propLiteToStack, vv.AnyType())

def propLiteToString(val):
  p = ChurchPrimeParser.instance()
  assert val.equal(vv.VentureValue.fromStackDict(p.parse_expression(p.unparse_expression(val.asStackDict()))))

