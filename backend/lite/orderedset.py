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


from collections import OrderedDict


class OrderedFrozenSet(object):
    """Variant of `frozenset` which remembers element insertion order.

    Iteration happens in order of insertion.
    """

    def __init__(self, iterable=None):
        self._dict = OrderedDict((x, 1) for x in iterable or ())

    def __iter__(self):
        return self._dict.iterkeys()

    def __len__(self):
        return len(self._dict)

    def __contains__(self, x):
        return x in self._dict

    def isdisjoint(self, other):
        for x in self._dict.iterkeys():
            if x in other:
                return False
        for x in other._dict.iterkeys():
            if x in self:
                return False
        return True

    def issubset(self, other):
        return self <= other

    def __le__(self, other):
        for x in self._dict.iterkeys():
            if x not in other:
                return False
        return True

    def __lt__(self, other):
        if not (self <= other):
            return False
        if all(x in self for x in other._dict.iterkeys()):
            return False
        return True

    def issuperset(self, other):
        return self >= other

    def __ge__(self, other):
        for x in other._dict.iterkeys():
            if x not in self:
                return False
        return True

    def __gt__(self, other):
        if not (self >= other):
            return False
        if all(x in other for x in self._dict.iterkeys()):
            return False
        return True

    def __eq__(self, other):
        if not self <= other:
            return False
        if not other <= self:
            return False
        for x, y in zip(self, other):
            if x != y:
                return False
        return True

    def union(self, *others):
        def union():
            for x in self:
                yield x
            for other in others:
                for x in other:
                    yield x
        return type(self)(union())

    def __or__(self, other):
        def union():
            for x in self:
                yield x
            for x in other:
                yield x
        return type(self)(union())

    def intersection(self, *others):
        assert all(isinstance(other, OrderedFrozenSet) for other in others)
        return type(self)(x for x in self
            if all(x in other for other in others))

    def __and__(self, other):
        return type(self)(x for x in self if x in other)

    def difference(self, *others):
        assert all(isinstance(other, OrderedFrozenSet) for other in others)
        return type(self)(x for x in self
            if not any(x in other for other in others))

    def __sub__(self, other):
        return type(self)(x for x in self if x not in other)

    def symmetric_difference(self, other):
        return self ^ other

    def __xor__(self, other):
        def symdiff():
            for x in self:
                if x not in other:
                    yield x
            for x in other:
                if x not in self:
                    yield x
        return type(self)(symdiff())

    def copy(self):
        return type(self)(self)

    def __repr__(self):
        return '%s([%s])' % \
            (type(self).__name__, ', '.join('%r' % (x,) for x in self))


class OrderedSet(OrderedFrozenSet):
    """Variant of `set` which remembers element insertion order.

    Iteration happens in order of insertion.  If an element is already
    in the set and is inserted again, there is no effect -- it retains
    its original place in the ordering.
    """

    def update(self, *others):
        for other in others:
            self |= other

    def __ior__(self, other):
        for x in other:
            self.add(x)

    def intersection_update(self, *others):
        for other in others:
            self &= other

    def __iand__(self, other):
        for x in self:
            if x not in other:
                self.remove(x)

    def difference_update(self, *others):
        for other in others:
            self -= other

    def __isub__(self, other):
        for x in other:
            self.discard(x)

    def symmetric_difference_update(self, other):
        self ^= other

    def __ixor__(self, other):
        self._dict = (self ^ other)._dict

    def add(self, x):
        self._dict[x] = 1

    def remove(self, x):
        del self._dict[x]

    def discard(self, x):
        if x in self:
            self.remove(x)

    def pop(self):
        x, _ = self._dict.pop()
        return x

    def clear(self):
        self._dict.clear()
