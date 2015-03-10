# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-

# Abstraction barrier for the Python dict representation of Venture values.

import numbers

def val(t,v):
  return {"type":t,"value":v}

def number(v):
  assert isinstance(v, numbers.Number)
  return val("number",v)

num = number

def real(v):
  assert isinstance(v, numbers.Number)
  return val("real",v)

def integer(v):
  assert isinstance(v, numbers.Number)
  return val("integer",v)

def probability(v):
  assert isinstance(v, numbers.Number)
  return val("probability",v)

def atom(v):
  assert isinstance(v, numbers.Number)
  return val("atom",v)

def boolean(v):
  assert isinstance(v, bool)
  return val("boolean",v)

def symbol(s):
  assert isinstance(s, basestring)
  return val("symbol",s)

sym = symbol

def blob(v):
  return val("blob",v)

python_list = list
def list(vs):
  return val("list", vs)

def dict(d):
  return val("dict", d)

def improper_list(vs, tail):
  return val("improper_list", (vs, tail))

def array(vs):
  return val("array", vs)

def array_unboxed(vs, subtype):
  ret = val("array_unboxed", vs)
  ret["subtype"] = subtype
  return ret

def vector(vs):
  return val("vector", vs)

def simplex(vs):
  return val("simplex", vs)

def matrix(vs):
  import numpy as np
  return val("matrix", np.asarray(vs))

def symmetric_matrix(vs):
  import numpy as np
  return val("symmetric_matrix", np.asarray(vs))

def quote(v):
  return [symbol("quote"), v]

def unquote(v):
  return [symbol("unquote"), v]

def quasiquote(v):
  import collections
  # TODO Nested quasiquotation
  def quotify(exp, to_quote):
    if to_quote:
      return quote(exp)
    else:
      return exp
  def quasiquoterecur(v):
    """Returns either (v, True), if quasiquotation reduces to quotation on
v, or (v', False), where v' is a directly evaluable expression that
will produce the term that the quasiquotation body v means."""
    if hasattr(v, "__iter__") and not isinstance(v, collections.Mapping):
      if len(v) > 0 and isinstance(v[0], collections.Mapping) and v[0]["type"] == "symbol" and v[0]["value"] == "unquote":
        return (v[1], False)
      else:
        answers = [quasiquoterecur(vi) for vi in v]
        if all([ans[1] for ans in answers]):
          return (v, True)
        else:
          return ([sym("list")] + [quotify(*ansi) for ansi in answers], False)
    else:
      return (v, True)
  return quotify(*quasiquoterecur(v))

def app(*items):
  return python_list(items) # Application is a Python list
