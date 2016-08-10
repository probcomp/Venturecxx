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

from venture.lite.wttree import PMap
from venture.lite.wttree import PSet
from venture.test.config import in_backend

@in_backend("none")
def testPMapInsertContainsDelete():
  r = PMap()
  assert len(r) == 0
  assert not r # Things with len == 0 register as False in Python

  r1 = r.insert(1,2)
  assert r1 # Things with len != 0 register as True
  assert len(r1) == 1
  assert 1 in r1
  assert r1.lookup(1) == 2
  assert len(r) == 0
  assert 1 not in r

  r2 = r1.delete(1)
  assert 1 in r1
  assert r1.lookup(1) == 2
  assert 1 not in r2
  assert r2.lookup(1) is None
  assert len(r2) == 0

  r3 = r1.adjust(1, lambda v: v+1)
  assert r1.lookup(1) == 2
  assert r3.lookup(1) == 3
  assert 1 not in r2

def _hash(i):
  return (i * 14536777) % 107331

@in_backend("none")
def testPMapStressInsertDelete():
  r = PMap()
  N = 1000
  for i in range(N):
    r = r.insert(_hash(i), i)

  for i in range(N):
    assert _hash(i) in r
    assert r.lookup(_hash(i)) == i

  r2 = r
  for i in range(N/2,N):
    r2 = r2.delete(_hash(i))

  for i in range(N/2):
    assert _hash(i) in r
    assert r.lookup(_hash(i)) == i
    assert _hash(i) in r2
    assert r2.lookup(_hash(i)) == i

  for i in range(N/2,N):
    assert _hash(i) in r
    assert r.lookup(_hash(i)) == i
    assert _hash(i) not in r2
    assert r2.lookup(_hash(i)) is None

@in_backend("none")
def testPMapIterate():
  r = PMap()
  N = 1000
  for i in range(N):
    r = r.insert(_hash(i), i)

  xs = dict()
  for (k,v) in r.iteritems(): xs[k] = v

  for i in range(N):
    assert xs[_hash(i)] == i

  ks = set()
  for k in r: ks.add(k)

  for i in range(N):
    assert _hash(i) in ks

@in_backend("none")
def testPSetInsertContainsDelete():
  r = PSet()
  assert len(r) == 0
  assert not r # Things with len == 0 register as False in Python

  r1 = r.insert(1)
  assert r1 # Things with len != 0 register as True
  assert len(r1) == 1
  assert 1 in r1
  assert len(r) == 0
  assert 1 not in r

  r2 = r1.delete(1)
  assert 1 in r1
  assert 1 not in r2
  assert len(r2) == 0

@in_backend("none")
def testPSetStressInsertDelete():
  r = PSet()
  N = 1000
  for i in range(N):
    r = r.insert(_hash(i))

  for i in range(N):
    assert _hash(i) in r

  r2 = r
  for i in range(N/2,N):
    r2 = r2.delete(_hash(i))

  for i in range(N/2):
    assert _hash(i) in r
    assert _hash(i) in r2

  for i in range(N/2,N):
    assert _hash(i) in r
    assert _hash(i) not in r2

@in_backend("none")
def testPSetIterate():
  r = PSet()
  N = 1000
  for i in range(N):
    r = r.insert(_hash(i))

  xs = set()
  for k in r: xs.add(k)

  for i in range(N):
    assert _hash(i) in xs

class Lose(object):
  def __init__(self, value):
    self._value = value
  @property
  def value(self):
    return self._value
  def __cmp__(self, other):
    raise Exception

@in_backend("none")
def testPMapKey():
  r = PMap(lambda x: x.value)
  r = r.insert(Lose(42), 'quagga')
  r = r.insert(Lose(54), 'moose')
  r = r.insert(Lose(50), 'caribou')
  r = r.delete(Lose(50))
  r = r.adjust(Lose(54), lambda s: s.replace('moose', 'eland'))
  it = iter(r)
  x = it.next()
  assert isinstance(x, Lose)
  assert x.value == 42
  x = it.next()
  assert isinstance(x, Lose)
  assert x.value == 54
  it = r.iteritems()
  x = it.next()
  assert len(x) == 2
  assert isinstance(x[0], Lose)
  assert x[0].value == 42
  assert x[1] == 'quagga'
  x = it.next()
  assert len(x) == 2
  assert isinstance(x[0], Lose)
  assert x[0].value == 54
  assert x[1] == 'eland'
