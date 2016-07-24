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

"""The VentureScript abstract syntax.

The abstract syntax is very simple.
- Python lists of abstract syntax are procedure and macro application
- Stack dicts of symbol type are variable references
- Everything else is a constant

Parsers emit abstract syntax trees annotated with location
information.  Each node in the returned syntax tree is a Located
object, carrying the raw abstract syntax and the location (as a 2-list
of the starting and ending character index, inclusive on both sides).

"""

from collections import namedtuple

Located = namedtuple("Located", ["loc", "value"])

def isloc(obj):
    return isinstance(obj, Located)

def update_value(located, v):
    return Located(located.loc, v)

def map_value(f, located):
    return Located(located.loc, f(located.value))

def loclist(items):
    """Locate a list of Located items.  The list spans the items' total extent.

Assumes the items are in ascending order of location.
"""
    assert len(items) >= 1
    (start, _) = items[0].loc
    (_, end) = items[-1].loc
    return Located([start, end], items)

def locmerge(lv0, lv1, v):
    "Construct a Located object with the given value that spans the extent of the given Located objects."
    (start, _) = lv0.loc
    (_, end) = lv1.loc
    assert start < end
    return Located([start, end], v)

def as_legacy_dict(located):
    if isinstance(located, Located):
        return {"value": as_legacy_dict(located.value), "loc": located.loc}
    elif isinstance(located, list) or isinstance(located, tuple):
        return [as_legacy_dict(v) for v in located]
    elif isinstance(located, dict):
        return dict((k, as_legacy_dict(v)) for k, v in located.iteritems())
    else:
        return located
