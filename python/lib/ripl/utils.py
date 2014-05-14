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

help_string = '''
Commands available from the prompt:

 help                         Show this help
 quit                         Exit Venture

Commands for modeling:

 assume symbol expression     Add the named variable to the model
 predict expression           Register the expression as a model prediction
 observe expression value     Condition on the expression being the value
 list-directives              List active directives and their current values
 forget number                Forget the given prediction or observation

Commands for inference:

 infer ct [kernel] [global?]  Run inference synchronously for ct steps
   `kernel' must be one of mh (default), pgibbs, gibbs, or meanfield
   `global?', if present, requests use of global scaffolds
     (not available for the gibbs kernel)
 start-ci [kernel] [global?]  Start continuous inference
 stop-ci                      Stop continuous inference
 ci-status                    Report status of continuous inference

Commands for interaction:

 sample expression            Sample the given expression immediately,
                                without registering it as a prediction
 force expression value       Set the given expression to the given value,
                                without conditioning on it
 list-directives              List active directives and their current values
 report number                Report the current value of the given directive
 global-log-score             Report current global log score
 clear                        Clear the entire current state
'''.strip()

def run_venture_console(ripl):
  done = False
  while not done:
    sys.stdout.write('>>> ')
    current_line = sys.stdin.readline()
    if not current_line:
      print ''
      print "End of input reached."
      print "Moriturus te saluto."
      break
    current_line = current_line.strip()
    if current_line == "":
      continue
    if current_line[0] == "(":
      current_line = current_line[1:-1]
    if current_line[0] == "[":
      current_line = current_line[1:-1]
    directive_and_content = current_line.split(" ", 1)
    directive_name = directive_and_content[0].lower()
    sys.stdout.write('')
    try:
      if directive_name == "quit":
        print "Moriturus te saluto."
        done = True
      elif directive_name == "help":
        print help_string
      elif directive_name == "list-directives":
        for d in ripl.list_directives():
          print d
      elif directive_name == "global-log-score":
        print ripl.get_global_logscore()
      elif directive_name == "ci-status":
        print ripl.continuous_inference_status()
      elif directive_name == "start-ci":
        args = current_line.split(" ")[1:]
        ripl.start_continuous_inference()
        print ripl.continuous_inference_status()
      elif directive_name == "stop-ci":
        ripl.stop_continuous_inference()
        print ripl.continuous_inference_status()
      elif directive_name == "clear":
        ripl.clear()
        print "Cleared trace."
      else:
        content = directive_and_content[1] if len(directive_and_content) >= 2 else None
        if directive_name == "assume":
          name_and_expression = content.split(" ", 1)
          print ripl.assume(name_and_expression[0], name_and_expression[1])
        elif directive_name == "predict":
          print ripl.predict(content)
        elif directive_name == "observe":
          expression_and_literal_value = content.rsplit(" ", 1)
          ripl.observe(expression_and_literal_value[0], expression_and_literal_value[1])
        elif directive_name == "forget":
          ripl.forget(int(content))
          print "Forgotten directive # {0}.".format(content)
        elif directive_name == "sample":
          print ripl.sample(content)
        elif directive_name == "force":
          expression_and_literal_value = content.rsplit(" ", 1)
          ripl.force(expression_and_literal_value[0], expression_and_literal_value[1])
        elif directive_name == "infer":
          command = expToDict(parse(content)) if content else None
          ripl.infer(command)
          print "Inferred according to %s." % ripl.parseInferParams(command)
        elif directive_name == "report":
          print ripl.report(int(content))
        else:
          print "Sorry, unknown directive."
    except Exception, err:
      print "Your query has generated an error:"
      traceback.print_exc()

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
      return str(token)

def unparse(exp):
  "Convert a Python object back into a Lisp-readable string."
  return '('+' '.join(map(unparse, exp))+')' if isinstance(exp, list) else str(exp)

def expToDict(exp):
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
    assert len(exp) == 4
    return {"kernel":"gibbs","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":False}
  elif tag == "slice":
    assert len(exp) == 4
    return {"kernel":"slice","scope":exp[1],"block":exp[2],"transitions":exp[3],"with_mutation":True}

  # [FIXME] expedient hack for now to allow windowing with pgibbs. 
  elif tag == "pgibbs":
    assert len(exp) == 5
    if type(exp[2]) is list:
      assert(exp[2][0] == "ordered_range")
      return {"kernel":"pgibbs","scope":exp[1],"block":"ordered_range",
              "min_block":exp[2][1],"max_block":exp[2][2],
              "particles":exp[3],"transitions":exp[4],"with_mutation":True}
    else: 
      return {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":exp[3],"transitions":exp[4],"with_mutation":True}

  elif tag == "func-pgibbs":
    assert len(exp) == 5
    return {"kernel":"pgibbs","scope":exp[1],"block":exp[2],"particles":exp[3],"transitions":exp[4],"with_mutation":False}
  elif tag == "meanfield":
    assert len(exp) == 5
    return {"kernel":"meanfield","scope":exp[1],"block":exp[2],"steps":exp[3],"transitions":exp[4]}
  elif tag == "hmc":
    assert len(exp) == 6
    return {"kernel":"hmc","scope":exp[1],"block":exp[2],"epsilon":exp[3],"L":exp[4],"transitions":exp[5]}
  elif tag == "map":
    assert len(exp) == 6
    return {"kernel":"map","scope":exp[1],"block":exp[2],"rate":exp[3],"steps":exp[4],"transitions":exp[5]}
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
      subkernels.append(expToDict(exp[1][k]))
    return {"kernel":"mixture","weights":weights,"subkernels":subkernels,"transitions":exp[2]}
  elif tag == "cycle":
    assert len(exp) == 3
    assert type(exp[1]) is list
    subkernels = [expToDict(e) for e in exp[1]]
    return {"kernel":"cycle","subkernels":subkernels,"transitions":exp[2]}
  elif tag == "resample":
    assert(len(exp) == 2)
    return {"command":"resample","particles":exp[1]}
  elif tag == "incorporate":
    assert(len(exp) == 1)
    return {"command":"incorporate"}
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
