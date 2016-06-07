# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from __future__ import division

import scipy.stats
import random

from nose import SkipTest
from nose.tools import assert_raises

from venture.lite.orderedset import OrderedFrozenSet
from venture.lite.orderedset import OrderedSet

def pick_integer(prng, k):
    return prng.randrange(k)

def pick_length(prng):
    return scipy.stats.nbinom(2, 1/5).rvs(size=1)[0]

def pick_elements(prng, k, g):
    l = [None] * k
    for i, x in enumerate(g):
        if i == k:
            break
        l[i] = x
    shuffle(prng, l)
    return l

def pick_sample(prng, k, l):
    sample = l[:k]
    for i in xrange(k, len(l)):
        j = pick_integer(prng, i + 1)
        if j < k:
            sample[j] = l[i]
    return sample

def shuffle(prng, l):
    for i, x in enumerate(l):
        j = pick_integer(prng, i + 1)
        l[i] = l[j]
        l[j] = x

def pick_permutation(n):
    p = list(range(n))
    shuffle(prng, p)
    return p

def pick_partition(prng, l):
    k = pick_integer(prng, len(l) + 1)
    return l[:k], l[k:]

def pick_subsets(prng, klass, generator):
    n = 3*pick_length(prng)
    elements = pick_elements(prng, n, generator)
    s = klass(elements)
    l_a, l_b0 = pick_partition(prng, elements)
    l_b, l_c = pick_partition(prng, l_b0)
    s_a = klass(l_a)
    s_b = klass(l_b)
    s_c = klass(l_c)
    s_ab = klass(l_a + l_b)
    s_ba = klass(l_b + l_a)
    s_bc = klass(l_b + l_c)
    s_cb = klass(l_c + l_b)
    s_ac = klass(l_a + l_c)
    s_ca = klass(l_c + l_a)
    s_abc = klass(l_a + l_b + l_c)
    s_acb = klass(l_a + l_c + l_b)
    s_bac = klass(l_b + l_a + l_c)
    s_bca = klass(l_b + l_c + l_a)
    s_cab = klass(l_c + l_a + l_b)
    s_cba = klass(l_c + l_b + l_a)
    for si in (s_a, s_b, s_c, s_ab, s_bc, s_ac, s_abc):
        check_order(elements, si)
    return elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
        s_abc, s_acb, s_bac, s_bca, s_cab, s_cba

def checkem(check):
    def integers(prng):
        i = 0
        while True:
            yield i
            i += 1
    def floats(prng):
        done = set()
        while True:
            x = prng.random()
            if x in done:
                continue
            done.add(x)
            yield x
    def chars(prng):
        done = set()
        for x in integers(prng):
            y = pick_integer(prng, 2)*32
            z = pick_integer(prng, 2)*1000
            c = unichr(x + y + z)
            if c in done:
                continue
            done.add(c)
            yield c
    def interleave(prng, generators):
        while True:
            for generator in generators:
                for x in generator(prng):
                    yield x
    def test():
        prng = random.Random()  # XXX nonreproducible
        klasses = (OrderedFrozenSet, OrderedSet)
        generators = (integers, floats, chars)
        for klass in klasses:
            for generator in generators:
                yield check, prng, klass, generator(prng)
            yield check, prng, klass, interleave(prng, generators)
    test.__name__ = check.__name__
    return test

def check_order(l, s):
    i = iter(l)
    for x in s:
        for y in i:
            if x == y:
                break
        else:
            raise Exception('fail %r' % (x,))

@checkem
def test_iter(prng, klass, generator):
    elements = pick_elements(prng, pick_length(prng), generator)
    s = klass(elements)
    for x, y in zip(elements, s):
        assert x == y
    check_order(elements, s)
    s = klass(elements + elements)
    for x, y in zip(elements, s):
        assert x == y
    check_order(elements, s)

@checkem
def test_len(prng, klass, generator):
    assert klass([0])
    assert not klass()
    assert not klass([])
    elements = pick_elements(prng, pick_length(prng), generator)
    s = klass(elements)
    assert len(s) == len(elements)
    s = klass(elements + elements)
    assert len(s) == len(elements)

@checkem
def test_contains(prng, klass, generator):
    elements = pick_elements(prng, pick_length(prng), generator)
    s = klass(elements)
    for x in elements:
        assert x in s
    for i, x in enumerate(generator):
        if i > 100:
            break
        assert x not in s

@checkem
def test_isdisjoint(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    assert s_a.isdisjoint(s_b)
    assert s_b.isdisjoint(s_a)

@checkem
def test_issubset(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            assert si.issubset(sj) == (si <= sj)
    assert s_a <= s_a
    assert not s_a or not s_a <= s_b
    assert not s_a or not s_a <= s_c
    assert not s_b or not s_b <= s_a
    assert s_b <= s_b
    assert not s_b or not s_b <= s_c
    assert not s_c or not s_c <= s_a
    assert not s_c or not s_c <= s_b
    assert s_c <= s_c
    assert not s_a or not s_a < s_a
    assert not s_a or not s_a < s_b
    assert not s_a or not s_a < s_c
    assert not s_b or not s_b < s_a
    assert not s_b or not s_b < s_b
    assert not s_b or not s_b < s_c
    assert not s_c or not s_c < s_a
    assert not s_c or not s_c < s_b
    assert not s_c or not s_c < s_c
    assert s_a <= s_ab
    assert not s_a or not s_a <= s_bc
    assert s_a <= s_ac
    assert s_b <= s_ab
    assert s_b <= s_bc
    assert not s_b or not s_b <= s_ac
    assert not s_c or not s_c <= s_ab
    assert s_c <= s_bc
    assert s_c <= s_ac

@checkem
def test_issuperset(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            assert si.issuperset(sj) == (si >= sj)
    assert s_a >= s_a
    assert not s_b or not s_a >= s_b
    assert not s_c or not s_a >= s_c
    assert not s_a or not s_b >= s_a
    assert s_b >= s_b
    assert not s_c or not s_b >= s_c
    assert not s_a or not s_c >= s_a
    assert not s_b or not s_c >= s_b
    assert s_c >= s_c
    assert not s_a or not s_a > s_a
    assert not s_b or not s_a > s_b
    assert not s_c or not s_a > s_c
    assert not s_a or not s_b > s_a
    assert not s_b or not s_b > s_b
    assert not s_c or not s_b > s_c
    assert not s_a or not s_c > s_a
    assert not s_b or not s_c > s_b
    assert not s_c > s_c
    assert s_ab >= s_a
    assert not s_a or not s_bc >= s_a
    assert s_ac >= s_a
    assert s_ab >= s_b
    assert s_bc >= s_b
    assert not s_b or not s_ac >= s_b
    assert not s_c or not s_ab >= s_c
    assert s_bc >= s_c
    assert s_ac >= s_c

@checkem
def test_union(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    assert s_a | s_b == s_ab
    assert s_b | s_c == s_bc
    assert s_a | s_c == s_ac
    assert s_ab | s_ab == s_ab
    assert s_ab | s_bc == s_abc
    assert s_ab | s_ac == s_abc
    assert s_bc | s_ac == s_bca
    assert s_bc | s_bc == s_bc
    assert s_bc | s_ac == s_bca
    assert s_ac | s_ab == s_acb
    assert s_ac | s_bc == s_acb
    assert s_ac | s_ac == s_ac
    for si in (s_ab, s_bc, s_ac):
        for sj in (s_ab, s_bc, s_ac):
            assert si.union(sj) == si | sj
            check_order(list(si) + list(sj), si | sj)

@checkem
def test_intersection(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    assert s_a & s_b == klass()
    assert s_b & s_c == klass()
    assert s_a & s_c == klass()
    assert s_ab & s_ab == s_ab
    assert s_ab & s_bc == s_b
    assert s_ab & s_ac == s_a
    assert s_bc & s_ac == s_c
    assert s_bc & s_bc == s_bc
    assert s_bc & s_ac == s_c
    assert s_ac & s_ab == s_a
    assert s_ac & s_bc == s_c
    assert s_ac & s_ac == s_ac
    for si in (s_ab, s_bc, s_ac):
        for sj in (s_ab, s_bc, s_ac):
            assert si.intersection(sj) == si & sj
            check_order(list(si) + list(sj), si & sj)

@checkem
def test_difference(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    assert s_a - s_b == s_a
    assert s_b - s_c == s_b
    assert s_a - s_c == s_a
    assert s_ab - s_ab == klass()
    assert s_ab - s_bc == s_a
    assert s_ab - s_ac == s_b
    assert s_bc - s_ac == s_b
    assert s_bc - s_bc == klass()
    assert s_bc - s_ac == s_b
    assert s_ac - s_ab == s_c
    assert s_ac - s_bc == s_a
    assert s_ac - s_ac == klass()
    for si in (s_ab, s_bc, s_ac):
        for sj in (s_ab, s_bc, s_ac):
            assert si.difference(sj) == si - sj
            check_order(list(si) + list(sj), si - sj)

@checkem
def test_symmetric_difference(prng, klass, generator):
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    assert s_a ^ s_b == s_ab
    assert s_b ^ s_c == s_bc
    assert s_a ^ s_c == s_ac
    assert s_ab ^ s_ab == klass()
    assert s_ab ^ s_bc == s_ac
    assert s_ab ^ s_ac == s_bc
    assert s_bc ^ s_ac == s_ba
    assert s_bc ^ s_bc == klass()
    assert s_bc ^ s_ac == s_ba
    assert s_ac ^ s_ab == s_cb
    assert s_ac ^ s_bc == s_ab
    assert s_ac ^ s_ac == klass()
    for si in (s_ab, s_bc, s_ac):
        for sj in (s_ab, s_bc, s_ac):
            assert si.symmetric_difference(sj) == si ^ sj
            check_order(list(si) + list(sj), si ^ sj)

@checkem
def test_copy(prng, klass, generator):
    n = pick_length(prng)
    elements = pick_elements(prng, n, generator)
    s = klass(elements)
    sc = s.copy()
    assert type(sc) == klass
    assert sc == s

@checkem
def test_ior(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            si_ = klass(si)
            si_ |= sj
            assert si_ == si | sj
            for sk in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
                si_ = klass(si)
                si_.update(sj, sk)
                assert si_ == si | sj | sk

@checkem
def test_iand(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            si_ = klass(si)
            si_ &= sj
            assert si_ == si & sj
            for sk in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
                si_ = klass(si)
                si_.intersection_update(sj, sk)
                assert si_ == si & sj & sk

@checkem
def test_isub(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            si_ = klass(si)
            si_ -= sj
            assert si_ == si - sj
            for sk in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
                si_ = klass(si)
                si_.difference_update(sj, sk)
                assert si_ == si - sj - sk

@checkem
def test_ixor(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements, s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca, \
      s_abc, s_acb, s_bac, s_bca, s_cab, s_cba = \
        pick_subsets(prng, klass, generator)
    for si in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
        for sj in (s_a, s_b, s_c, s_ab, s_ba, s_bc, s_cb, s_ac, s_ca):
            si_ = klass(si)
            si_ ^= sj
            assert si_ == si ^ sj
            si_ = klass(si)
            si_.symmetric_difference_update(sj)
            assert si_ == si ^ sj

@checkem
def test_addremove(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements = pick_elements(prng, 1 + pick_length(prng), generator)
    s = klass(elements[1:])
    x = elements[0]
    assert x not in s
    s.add(x)
    assert x in s
    s.remove(x)
    assert x not in s

@checkem
def test_remove(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements = pick_elements(prng, 1 + pick_length(prng), generator)
    s = klass(elements[1:])
    x = elements[0]
    assert x not in s
    assert_raises(KeyError, s.remove, x)

@checkem
def test_discard(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements = pick_elements(prng, 1 + pick_length(prng), generator)
    s = klass(elements[1:])
    x = elements[0]
    assert x not in s
    s.discard(x)
    assert x not in s

@checkem
def test_pop(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements = pick_elements(prng, pick_length(prng), generator)
    s = klass(elements)
    for x in elements:
        y = s.pop()
        assert x == y

@checkem
def test_clear(prng, klass, generator):
    if klass == OrderedFrozenSet:
        raise SkipTest('destructive operations')
    elements = pick_elements(prng, 1 + pick_length(prng), generator)
    s = klass(elements)
    assert s
    assert 0 < len(s)
    s.clear()
    assert not s
    assert 0 == len(s)
