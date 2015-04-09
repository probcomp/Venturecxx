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

"""Mutable Lenses.

A "lens" on some part of some value is, loosely speaking, a way to
"focus" on that part, so that you can see and modify it in isolation
from the rest, but have your modifications appear in said rest.

The idea of (functional) lenses has been floating around the
functional programming community for a while; I began learning it from
Ed Kmett's exhautive `lens` package: https://github.com/ekmett/lens

Lenses are actually easier to conceptualize in an imperative languge,
because the part about "have your modifications appear" is natural in
the imperative world -- just write the relevant part of the structure.
So in the imperative world, a lens can be thought of as just a path to
a place that's good for either reading or writing.  (See setf methods
in Common Lisp).

This module defines an interface and some combinators for a very
unelaborated mutable lens system for use in the Venture implementation."""

import itertools

class MLens(object):
  """A mutable lens interface.

  Implementations should respect the lens laws:
  1) You get out what you put in:
     lens.set(a)
     assert lens.get() == a
  2) Putting back what you got changes nothing:
     { a = lens.get(); lens.set(a) } = {}
  3) Writing twice is the same as writing once:
     { lens.set(a); lens.set(b) } = { lens.set(b) }"""

  def get(self):
    """Read the value the lens points to."""
    raise Exception("Called abstract method get of MLens")
  def set(self, _new):
    """Write a new value into the lens."""
    raise Exception("Called abstract method set of MLens")

def real_lenses(thing):
  """Return a list of all lenses on real values in the given object, in order.
  
  This is really "flat_map (lambda t: t.real_lenses())", but there
  doesn't seem to be a good way to write it that way in Python.

  """
  if hasattr(thing, "real_lenses"):
    return thing.real_lenses()
  elif hasattr(thing, "__iter__"):
    return list(itertools.chain(*[real_lenses(t) for t in thing]))
  else:
    return []
