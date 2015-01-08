# Inference-program macros.

# Perhaps this should be unified with the modeling language macros
# that are expanded by venture.sivm.macro (first).  One difference:
# this code does not conserve expression indexes the way the sivm
# macro expander does.  This is probably a bug.

import venture.value.dicts as v

def macroexpand_inference(program):
  if type(program) is list and len(program) == 0:
    return program
  elif type(program) is list and type(program[0]) is dict and program[0]["value"] in macros:
    return macros[program[0]["value"]](program)
  elif type(program) is list: return [macroexpand_inference(p) for p in program]
  else: return program

macro_list = []
macros = {}

def register_macro(name, func):
  macro_list.append((name, func))
  macros[name] = func

def begin_macro(program):
  assert len(program) >= 2
  return [v.sym("sequence"), [v.sym("list")] + [macroexpand_inference(e) for e in program[1:]]]
register_macro("begin", begin_macro)

def cycle_macro(program):
  assert len(program) == 3
  subkernels = macroexpand_inference(program[1])
  transitions = macroexpand_inference(program[2])
  return [program[0], [v.sym("list")] + subkernels, transitions]
register_macro("cycle", cycle_macro)

def mixture_macro(program):
  assert len(program) == 3
  weights = []
  subkernels = []
  weighted_ks = macroexpand_inference(program[1])
  transitions = macroexpand_inference(program[2])
  for i in range(len(weighted_ks)/2):
    j = 2*i
    k = j + 1
    weights.append(weighted_ks[j])
    subkernels.append(weighted_ks[k])
  return [program[0], [v.sym("simplex")] + weights, [v.sym("array")] + subkernels, transitions]
register_macro("mixture", mixture_macro)

def quasiquotation_macro(min_size = None, max_size = None):
  def the_macro(program):
    if min_size is not None:
      assert len(program) >= min_size
    if max_size is not None:
      assert len(program) <= max_size
    return [program[0]] + [v.quasiquote(e) for e in program[1:]]
  return the_macro
register_macro("peek", quasiquotation_macro(2))
register_macro("printf", quasiquotation_macro(2))
register_macro("plotf", quasiquotation_macro(2))
register_macro("plotf_to_file", quasiquotation_macro(2))
register_macro("call_back", quasiquotation_macro(2))
register_macro("call_back_accum", quasiquotation_macro(2))
register_macro("assume", quasiquotation_macro(3, 3))
register_macro("predict", quasiquotation_macro(2, 2))

def observe_macro(program):
  assert len(program) == 3
  return [program[0], v.quasiquote(program[1]), macroexpand_inference(program[2])]
register_macro("observe", observe_macro)
