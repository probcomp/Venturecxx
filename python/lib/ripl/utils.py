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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
import venture.sivm.core_sivm as core_sivm

def _strip_types(value):
    if isinstance(value, dict) and "type" in value and "value" in value:
        return _strip_types(value['value'])
    if isinstance(value,list):
        return [_strip_types(v) for v in value]
    return value

def _strip_types_from_dict_values(value):
    return dict([(k, _strip_types(v)) for (k,v) in value.iteritems()])

# This list of functions defines the public REST API
# of the Ripl server and client
#
# could have used inspection to generate this list
# of functions, but being explicit is better/more secure
_RIPL_FUNCTIONS = [
        'get_mode','list_available_modes','set_mode',
        'execute_instruction','execute_program','substitute_params',
        'split_program','get_text','character_index_to_expression_index',
        'expression_index_to_text_index','assume','predict',
        'observe','configure','forget','report','infer',
        'clear','rollback','list_directives','get_directive',
        'force','sample','continuous_inference_status',
        'start_continuous_inference','stop_continuous_inference',
        'get_current_exception','get_state','get_logscore',
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

def expToDict(exp):
  if isinstance(exp, int):
    return {"kernel":"mh", "scope":"default", "block":"one", "transitions": exp}
  tag = exp[0]
  if tag == "mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "func_mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "gibbs":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"gibbs","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    return ans
  elif tag == "emap":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"emap","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    return ans
  elif tag == "slice":
    assert len(exp) == 6
    return {"kernel":"slice","scope":exp[1],"block":exp[2],"w":exp[3],"m":int(exp[4]),"transitions":int(exp[5])}
  # [FIXME] expedient hack for now to allow windowing with pgibbs.
  elif tag == "pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    if type(exp[2]) is list:
      assert exp[2][0] == "ordered_range"
      ans = {"kernel":"pgibbs","scope":exp[1],"block":"ordered_range",
            "min_block":exp[2][1],"max_block":exp[2][2],
            "particles":int(exp[3]),"transitions":int(exp[4])}
    else:
      ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    return ans
  elif tag == "func_pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":int(exp[3]),"transitions":int(exp[4])}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    return ans
  elif tag == "meanfield":
    assert len(exp) == 5
    return {"kernel":"meanfield","scope":exp[1],"block":exp[2],"steps":int(exp[3]),"transitions":int(exp[4])}
  elif tag == "hmc":
    assert len(exp) == 6
    return {"kernel":"hmc","scope":exp[1],"block":exp[2],"epsilon":exp[3],"L":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "map":
    assert len(exp) == 6
    return {"kernel":"map","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "nesterov":
    assert len(exp) == 6
    return {"kernel":"nesterov","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":int(exp[4]),"transitions":int(exp[5])}
  elif tag == "latents":
    assert len(exp) == 4
    return {"kernel":"latents","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
  elif tag == "rejection":
    assert len(exp) >= 3
    assert len(exp) <= 4
    if len(exp) == 4:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":int(exp[3])}
    else:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":1}
  else:
    raise Exception("Cannot parse infer instruction")
