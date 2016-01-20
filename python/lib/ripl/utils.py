# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

def strip_types(value):
    if isinstance(value, dict) and "type" in value and "value" in value:
        return strip_types(value['value'])
    if isinstance(value,list):
        return [strip_types(v) for v in value]
    return value

def strip_types_from_dict_values(value):
    return dict([(k, strip_types(v)) for (k,v) in value.iteritems()])

# This list of functions defines the public REST API
# of the Ripl server and client
#
# could have used inspection to generate this list
# of functions, but being explicit is better/more secure
_RIPL_FUNCTIONS = [
        'get_mode','list_available_modes','set_mode',
        'execute_instruction','execute_program',
        'split_program','get_text',
        'expression_index_to_text_index','assume','predict',
        'observe','forget','report','infer',
        'clear','list_directives','get_directive',
        'force','sample','continuous_inference_status',
        'start_continuous_inference','stop_continuous_inference',
        'get_global_logscore'
        ]

def read(s):
  "Read a Scheme expression from a string."
  return read_from(tokenize(s))

parse = read

def tokenize(s):
  "Convert a string into a list of tokens."
  return s.replace('(',' ( ').replace(')',' ) ').split()

def read_from(tokens):
  "Read an expression from a sequence of tokens."
  if len(tokens) == 0:
    raise SyntaxError('unexpected EOF while reading')
  token = tokens.pop(0)
  if '(' == token:
    L = []
    while tokens[0] != ')':
      L.append(read_from(tokens))
    tokens.pop(0) # pop off ')'
    return L
  elif ')' == token:
    raise SyntaxError('unexpected )')
  else:
    return atom(token)

def atom(token):
  "Numbers become numbers; every other token is a symbol."
  try: return int(token)
  except ValueError:
    try: return float(token)
    except ValueError:
      if token.lower() == "true": return True
      if token.lower() == "false": return False
      return str(token)

def unparse(exp):
  "Convert a Python object back into a Lisp-readable string."
  return '('+' '.join(map(unparse, exp))+')' if isinstance(exp, list) else str(exp)
