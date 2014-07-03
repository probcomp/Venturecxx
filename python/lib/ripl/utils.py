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

## TODO Define a VentureScript version of this parser
def expToDict(exp, ripl=None):
  def _mimic_parser(exp):
    return core_sivm._modify_expression(ripl._ensure_parsed_expression(exp))
  def default_name_for_exp(exp):
    if isinstance(exp, basestring):
      return exp
    elif hasattr(exp, "__iter__"):
      return "(" + ' '.join([default_name_for_exp(e) for e in exp]) + ")"
    else:
      return str(exp)
  if isinstance(exp, int):
    return {"transitions": exp}
  tag = exp[0]
  if tag == "mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":True}
  elif tag == "func-mh":
    assert len(exp) == 4
    return {"kernel":"mh","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":False}
  elif tag == "gibbs":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"gibbs","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":False}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    return ans
  elif tag == "emap":
    assert 4 <= len(exp) and len(exp) <= 5
    ans = {"kernel":"emap","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":False}
    if len(exp) == 5:
      ans["in_parallel"] = exp[4]
    return ans
  elif tag == "slice":
    assert len(exp) == 4
    return {"kernel":"slice","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":True}
  # [FIXME] expedient hack for now to allow windowing with pgibbs. 
  elif tag == "pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    if type(exp[2]) is list:
      assert exp[2][0] == "ordered_range"
      ans = {"kernel":"pgibbs","scope":exp[1],"block":"ordered_range",
            "min_block":exp[2][1],"max_block":exp[2][2],
            "particles":exp[3],"transitions":exp[4],"with_mutation":True}
    else: 
      ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":exp[3],"transitions":exp[4],"with_mutation":True}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    return ans
  elif tag == "func-pgibbs":
    assert 5 <= len(exp) and len(exp) <= 6
    ans = {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":exp[3],"transitions":exp[4],"with_mutation":False}
    if len(exp) == 6:
      ans["in_parallel"] = exp[5]
    return ans
  elif tag == "meanfield":
    assert len(exp) == 5
    return {"kernel":"meanfield","scope":exp[1],"block":exp[2],"steps":exp[3],"transitions":exp[4]}
  elif tag == "hmc":
    assert len(exp) == 6
    return {"kernel":"hmc","scope":exp[1],"block":exp[2],"epsilon":exp[3],"L":exp[4],"transitions":exp[5]}
  elif tag == "map":
    assert len(exp) == 6
    return {"kernel":"map","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":exp[4],"transitions":exp[5]}
  elif tag == "nesterov":
    assert len(exp) == 6
    return {"kernel":"nesterov","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":exp[4],"transitions":exp[5]}
  elif tag == "latents":
    assert len(exp) == 4
    return {"kernel":"latents","scope":exp[1],"block":exp[2],"transitions":exp[3]}
  elif tag == "rejection":
    assert len(exp) >= 3
    assert len(exp) <= 4
    if len(exp) == 4:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":exp[3]}
    else:
      return {"kernel":"rejection","scope":exp[1],"block":exp[2],"transitions":1}
  elif tag == "mixture":
    assert len(exp) == 3
    weights = []
    subkernels = []
    assert type(exp[1]) is list
    for i in range(len(exp[1])/2):
      j = 2*i
      k = j + 1
      weights.append(exp[1][j])
      subkernels.append(expToDict(exp[1][k]), ripl)
    return {"kernel":"mixture","weights":weights,"subkernels":subkernels,"transitions":exp[2]}
  elif tag == "cycle":
    assert len(exp) == 3
    assert type(exp[1]) is list
    subkernels = [expToDict(e, ripl) for e in exp[1]]
    return {"kernel":"cycle","subkernels":subkernels,"transitions":exp[2]}
  elif tag == "resample":
    assert len(exp) == 2
    return {"command":"resample","particles":exp[1]}
  elif tag == "incorporate":
    assert len(exp) == 1
    return {"command":"incorporate"}
  elif tag == "peek" or tag == "peek-all":
    assert 2 <= len(exp) and len(exp) <= 3
    if len(exp) == 2:
      name = default_name_for_exp(exp[1])
    else:
      name = exp[2]
    if ripl is not None:
      expr = _mimic_parser(exp[1])
    else:
      raise Exception("Need a ripl around in order to parse model expressions in inference expressions")
    return {"command":tag, "expression":expr, "name":name}
  elif tag == "plotf":
    assert len(exp) >= 2
    return {"command":"plotf", "specification":exp[1], "names":[default_name_for_exp(e) for e in exp[2:]], "expressions": [_mimic_parser(e) for e in exp[2:]]}
  else:
    raise Exception("Cannot parse infer instruction")

def testHandInspect():
  k1 = "(mh 11 22 33)"
  k2 = "(pgibbs 11 22 33 44)"
  k3 = "(meanfield 11 22 33 44)"
  k4 = "(latents 11 22 33)"
  k5 = "(rejection 11 22 33)"
  k6 = "(resample 11)"
  k7 = "(incorporate)"

  print k1,expToDict(parse(k1))
  print k2,expToDict(parse(k2))
  print k3,expToDict(parse(k3))
  print k4,expToDict(parse(k4))
  print k5,expToDict(parse(k5))
  print k6,expToDict(parse(k4))
  print k7,expToDict(parse(k5))
  print "----------------------"
  print expToDict(parse("(cycle (%s %s) 100)" % (k1,k2)))
  print expToDict(parse("(mixture (.1 %s .9 %s) 100)" % (k1,k2)))
  print expToDict(parse("(cycle (%s (mixture (.1 %s .9 %s) 100)) 1000)" % (k1,k2,k3)))
