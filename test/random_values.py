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

"""Random Venture values and programs.
"""

import numpy.random as npr
from venture.lite import value as v
from venture.lite import types as t
from venture.lite.utils import normalizeList
from venture.lite import env as env

class DefaultRandomVentureValue(object):
  def __init__(self, method, **kwargs):
    self.method = method
    self.kwargs = kwargs
  def generate(self, **kwargs):
    return getattr(self, self.method)(**(dict(self.kwargs.items() + kwargs.items())))
  def number(self, **_kwargs):
    return v.VentureNumber(npr.uniform(-10, 10))
  def integer(self, **_kwargs):
    return v.VentureInteger(npr.choice(range(-10, 10)))
  def count(self, **_kwargs):
    return v.VentureInteger(npr.choice(range(10)))
  def positive(self, **_kwargs):
    return v.VentureNumber(npr.uniform(0, 10)) # TODO Prevent zero
  def probability(self, **_kwargs):
    return v.VentureProbability(npr.uniform(0, 1))
  def atom(self, **_kwargs):
    return v.VentureAtom(npr.randint(0, 11)) # Open at the top
  def bool(self, **_kwargs):
    return v.VentureBool(npr.choice([False, True]))
  def zero(self, **_kwargs):
    return 0 # A gradient in an empty vector space
  def symbol(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(1, 10)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return v.VentureSymbol(''.join(npr.choice(list(alphabet), length)))
  def string(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(1, 10)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return v.VentureString(''.join(npr.choice(list(alphabet), length)))
  def array(self, length=None, elt_dist=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.VentureArray([elt_dist.generate(**kwargs) for _ in range(length)])
  def array_unboxed(self, length=None, elt_type=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_type is None:
      elt_type = t.NumberType() # TODO Do I want to test on a screwy class of unboxed arrays in general?
    return v.VentureArrayUnboxed([elt_type.asPython(elt_type.distribution(self.__class__, **kwargs).generate()) for _ in range(length)], elt_type)
  def nil(self, **_kwargs):
    return v.VentureNil()
  def pair(self, size=None, first_dist=None, second_dist=None, **kwargs):
    if size is None:
      size = npr.randint(0, 30)
    left_size = npr.randint(0, size+1)
    if first_dist is None:
      first_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    if second_dist is None:
      second_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.VenturePair((first_dist.generate(size=left_size, **kwargs),
                          second_dist.generate(size=size-left_size, **kwargs)))
  def simplex(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    return v.VentureSimplex(normalizeList(npr.uniform(0, 1, length)))
  def dict(self, **_kwargs):
    raise Exception("Can't synthesize dicts yet")
  def mapping(self, **kwargs):
    # TODO Only synthesize a mapping of a type that is compatible with
    # the intended keys (i.e., no arrays with symbol keys).
    # For that, I need to capture the non-independence between the
    # types of different arguments to the same procedure.
    # TODO Be willing to synthesize dicts and environments
    # kind = npr.choice(["dict", "list", "array", "environment"])
    kind = npr.choice(["list", "array"])
    return getattr(self, kind)(**kwargs)
  def matrix(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(1, 10)
    return v.VentureMatrix(npr.uniform(-10, 10, (length, length))) # Square matrices
  def symmetricmatrix(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(1, 10)
    candidate = npr.uniform(-10, 10, (length, length)) # Square matrices
    return v.VentureSymmetricMatrix((candidate + candidate.transpose()) / 2)
  def sp(self, **_kwargs):
    raise Exception("Can't synthesize SPs")
  def environment(self, **_kwargs):
    # TODO Implement a more interesting distribution on environments
    return env.VentureEnvironment()
  def list(self, length=None, elt_dist=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.pythonListToVentureList([elt_dist.generate(**kwargs) for _ in range(length)])
  def exp(self, **_kwargs):
    # TODO Synthesizing interesting expressions is the fun part!
    return self.list(length=0)
  def object(self, depth=None, **kwargs):
    if depth is None:
      depth = npr.randint(0, 5)
    if depth == 0:
      return getattr(self, npr.choice(["number", "integer", "probability", "atom", "bool", "symbol", "string", "nil"]))(**kwargs)
    else:
      return getattr(self, npr.choice(["pair", "list", "array", "array_unboxed", "simplex", "matrix", "symmetricmatrix"]))(depth=depth-1, **kwargs)
