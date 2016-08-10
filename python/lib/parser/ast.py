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

"""Location-annotated VentureScript abstract syntax, as produced by parsers.

Is you are writing a parser for a VentureScript sublanguage, produce
`Located` objects as described here.

The bare abstract syntax of Venture is a recursive structure described
in `venture.value.dicts`.  Parsers emit abstract syntax trees
annotated with location information.  Each node in the returned syntax
tree is a `Located` object, carrying the raw abstract syntax and the
location (as a 2-list of the starting and ending character index,
inclusive on both sides).  For example, the parse for ``1 + 2`` would be
constructed as::

    import venture.value.dicts as e

    one  = Located([0, 0], e.number(1))
    plus = Located([2, 2], e.symbol("+"))
    two  = Located([4, 4], e.number(2))
    Located([0, 4], e.app(plus, one, two))
"""

from collections import namedtuple

Located = namedtuple("Located", ["loc", "value"])

def isloc(obj):
    "Check whether the given object is a `Located` instance."
    return isinstance(obj, Located)

def update_value(located, v):
    "Return a new `Located` instance with the same location and a new value."
    return Located(located.loc, v)

def map_value(f, located):
    """Return a new `Located` instance with the same location and a computed value.

    The new value is computed by applying ``f`` to the value in ``located``."""
    return Located(located.loc, f(located.value))

def loclist(items):
    """Create a `Located` list of `Located` items.  The list spans the items' total extent.

Assumes the items are in ascending order of location.
"""
    assert len(items) >= 1
    (start, _) = items[0].loc
    (_, end) = items[-1].loc
    return Located([start, end], items)

def locmerge(lv0, lv1, v):
    """Create a `Located` object with the given value.

    The extent the result spans the extent of the two given `Located`
    objects, which must be in location order.
    """
    (start, _) = lv0.loc
    (_, end) = lv1.loc
    assert start < end
    return Located([start, end], v)

def as_legacy_dict(located):
    """Convert a `Located` object to a legacy Python dict representation.

    New code should not use this."""
    if isinstance(located, Located):
        return {"value": as_legacy_dict(located.value), "loc": located.loc}
    elif isinstance(located, list) or isinstance(located, tuple):
        return [as_legacy_dict(v) for v in located]
    elif isinstance(located, dict):
        return dict((k, as_legacy_dict(v)) for k, v in located.iteritems())
    else:
        return located
