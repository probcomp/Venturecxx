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

# Abstraction barrier for the Python dict representation of Venture values.

import numbers

python_list = list
python_dict = dict

NO_PARSE_EXPRESSION = {None: "__NO_PARSE_EXPRESSION__"}

def val(t,v):
  return {"type":t,"value":v}

def is_val(obj):
  """Checks whether the outermost layer of obj looks like it could
validly be a stack dict representation of something.

(That is, Python lists are ok, because those represent arrays.)"""
  return is_stack_dict(obj) or isinstance(obj, list)

def is_stack_dict(obj):
  """Checks whether the outermost layer of obj looks like an actual stack dict."""
  return isinstance(obj, python_dict) and "type" in obj and "value" in obj

def is_stack_dict_of_type(tp, obj):
  return is_stack_dict(obj) and obj["type"] is tp

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

def string(s):
  assert isinstance(s, basestring)
  return val("string",s)

def blob(v):
  return val("blob",v)

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

def sp(v, aux=None):
  candidate = {"type":"sp", "value":v}
  if aux is not None:
    candidate["aux"] = aux
  return candidate

def quote(v):
  return [symbol("quote"), v]

def quasiquote(v):
  return [symbol("quasiquote"), v]

def unquote(v):
  return [symbol("unquote"), v]

def app(*items):
  return python_list(items) # Application is a Python list
