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
# -*- coding: utf-8 -*-

"""Programmatically construct literal Venture values and unannotated Venture abstract syntax.

If you are writing a parser for a VentureScript sublanguage, see
`venture.parser.ast` for annotating the abstract syntax tree with the
location information the parser expects.

The main elements of constructing bare abstract syntax are

- `symbol` or `sym` for variables

- `app` for combining forms

- the other functions (`number`, `boolean`, etc) for literals

Shortcuts for `quote`, `quasiquote`, and `unquote` are provided as
conveniences, since those forms occur often in programmatically
constructed expressions.
"""

import numbers

python_list = list
python_dict = dict

def number(v):
  """Construct a Venture (floating-point) number.

  Venture numbers are self-evaluating."""
  assert isinstance(v, numbers.Number)
  return val("number",v)

num = number
real = number

def integer(v):
  """Construct a Venture integer.

  Venture integers are self-evaluating.
  """
  assert isinstance(v, numbers.Number)
  return val("integer",v)

def probability(v):
  """Construct a Venture probability value.

Currently, these are represented as (floating-point) numbers, but
something like log-odds space may prove appropriate in the future.

Venture probabilities are self-evaluating.
  """
  assert isinstance(v, numbers.Number)
  assert 0 <= v and v <= 1
  return val("number",v)

def atom(v):
  """Construct a Venture atom.

  Venture atoms are self-evaluating."""
  assert isinstance(v, numbers.Number)
  return val("atom",v)

def boolean(v):
  """Construct a Venture boolean.

  Venture booleans are self-evaluating."""
  assert isinstance(v, bool)
  return val("boolean",v)

def symbol(s):
  """Construct a Venture symbol.

  A symbol represents a variable name, which is looked up in the
  lexical environment when the symbol is evaluated.
  """
  assert isinstance(s, basestring)
  return val("symbol",s)

sym = symbol

def string(s):
  """Construct a Venture string.

  Venture strings are self-evaluating."""
  assert isinstance(s, basestring)
  return val("string",s)

def blob(v):
  """Construct a Venture blob.

  The object ``v`` becomes the payload of the blob, which Venture will
  carry around without inspecting.  This is useful in conjunction with
  foreign SPs that can interpret the payload.

  Venture blobs are self-evaluating.
  """
  return val("blob",v)

def array(vs):
  """Construct a Venture array.

  The ``vs`` argument must be a Python sequence of Venture objects
  (constructed with other functions from this module).

  Arrays are combining forms when evaluated.  The meaning of the array
  depends on the first element---if it is the name of a macro or
  special form, it will be evaluated accordingly.  Otherwise, an array
  is an application.

  A array quoted with `quote` will evaluate to a Venture array object.

  """
  return val("array", vs)

def array_unboxed(vs, subtype):
  """Construct an unboxed Venture array.

  The ``vs`` argument must be a Python sequence of Python objects,
  suitable for interpretation as Venture objects as by calling `val`
  with the ``subtype`` argument.

  An unboxed array is semantically equivalent to the boxed array
  that would be constructed by `array([val(subype, v) for v in vs])`
  but more efficient.

  Unquoted unboxed arrays are evaluated like arrays, which is usually not what
  is desired.
  """
  ret = val("array_unboxed", vs)
  ret["subtype"] = subtype
  return ret

def vector(vs):
  """Construct a Venture vector.

  The ``vs`` argument must be a Python sequence of numbers.

  Unquoted vectors are evaluated like arrays, which is usually not
  what is desired.
  """
  return val("vector", vs)

def simplex(vs):
  """Construct a Venture simplex.

  The ``vs`` argument must be a Python sequence of numbers between 0
  and 1.

  Unquoted simplexes are evaluated like arrays, which is usually not
  what is desired.
  """
  return val("simplex", vs)

def list(vs):
  """Construct a Venture list.

  The ``vs`` argument must be a Python sequence of Venture objects
  (constructed with other functions from this module).

  Lists are combining forms when evaluated.  The meaning of the list
  depends on the first element---if it is the name of a macro or
  special form, it will be evaluated accordingly.  Otherwise, a list
  is an application.

  A list quoted with `quote` will evaluate to a Venture list object.

  """
  return val("list", vs)

def dict(d):
  """Construct a Venture dictionary.

  The argument ``d`` must be a Python dictionary whose keys and values
  are Venture objects (constructed with other functions from this
  module).

  Venture dictionaries are self-evaluating.

  """
  return val("dict", d)

def improper_list(vs, tail):
  """Construct an improper Venture list.

  An improper list is one whose last pair has something other than
  `nil` in its `second` field.  You only need this if you know you
  need it.

  Improper lists are combining forms if the tail is a list (making the
  full list proper after all) or an array.

  It is an error to evaluate an improper list that is not a combining
  form.
  """
  return val("improper_list", (vs, tail))

def matrix(vs):
  """Construct a Venture matrix.

  The ``vs`` argument must be a Python data structure suitable for
  conversion to a two-dimensional array with `numpy.asarray`.

  Venture matrices are self-evaluating.
  """
  import numpy as np
  return val("matrix", np.asarray(vs))

def symmetric_matrix(vs):
  """Construct a Venture symmetric matrix.

  The ``vs`` argument must be a Python data structure suitable for
  conversion to a two-dimensional array with `numpy.asarray`.

  Venture symmetric matrices are self-evaluating.
  """
  import numpy as np
  return val("symmetric_matrix", np.asarray(vs))

def sp(v, aux=None):
  """Construct a Venture stochastic procedure.

  Foreign SPs are usually installed with
  :py:meth:`venture.ripl.ripl.Ripl.bind_foreign_sp` and
  :py:meth:`venture.ripl.ripl.Ripl.bind_foreign_inference_sp` rather
  than direct insertion into source code.

  The ``v`` argument must be an instance of `venture.lite.sp.SP`.  The
  `aux` argument, if supplied, becomes the procedure's auxiliary state
  (see `venture.lite.sp.SP`).

  Venture SPs are self-evaluating.
  """
  candidate = {"type":"sp", "value":v}
  if aux is not None:
    candidate["aux"] = aux
  return candidate

def app(*items):
  """Construct a Venture combining form.

  Each item must be a Venture object, as constructed by functions in
  this module.

  Note that the result will not be evaluated as an application if the
  first item is a symbol which is a macro name or special form.
  """
  return python_list(items) # Application is a Python list

def quote(v):
  """Construct a Venture quotation form.

  The item ``v`` must be a Venture object, as constructed by functions
  in this module.

  The result will evaluate to a literal representation of ``v``, even if
  ``v`` would otherwise be treated as a combining form.

  This is equivalent to constructing an application of the `quote`
  special form.
  """
  return [symbol("quote"), v]

def quasiquote(v):
  """Construct a Venture quasiquotation form.

  The item ``v`` must be a Venture object, as constructed by functions
  in this module.

  This is equivalent to constructing an application of the
  `quasiquote` macro.
  """
  return [symbol("quasiquote"), v]

def unquote(v):
  """Construct a Venture unquotation form.

  The item ``v`` must be a Venture object, as constructed by functions
  in this module.

  This is equivalent to constructing an application of the `unquote`
  macro.  It only has meaning inside a `quasiquote`, but note that
  many modeling forms (`assume`, `observe`, etc) implicitly quasiquote
  their expression arguments.
  """
  return [symbol("unquote"), v]

def val(t, v):
  """Construct a Venture value of type ``t``, with content ``v``.

  The valid user-given types are

  - "number"
  - "integer"
  - "atom"
  - "boolean"
  - "symbol"
  - "string"
  - "blob"
  - "array"
  - "vector"
  - "simplex"
  - "list"
  - "dict"
  - "improper_list" (v must be a 2-tuple of the proper part and the tail)
  - "matrix"
  - "symmetric_matrix"
  - "sp" (``aux`` cannot be supplied)

  The effect is the same as calling that function from this module.
"""
  return {"type":t, "value":v}

def is_val(obj):
  """Checks whether ``obj`` is a valid unannotated Venture syntax object.

  Only checks the top level, not recursively."""
  # Python lists are ok, because those represent arrays.
  return is_basic_val(obj) or isinstance(obj, python_list)

def is_basic_val(obj):
  """Checks whether ``obj`` is a valid unannotated literal Venture object.

  Only checks the top level, not recursively."""
  return isinstance(obj, python_dict) and "type" in obj and "value" in obj

def is_basic_val_of_type(tp, obj):
  """Checks whether ``obj`` is a valid unannotated literal Venture object of the given type.

  Only checks the top level, not recursively.  Types as in `val`."""
  return is_basic_val(obj) and obj["type"] is tp
