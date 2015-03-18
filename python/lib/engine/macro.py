# Inference-program macros.

# Perhaps this should be unified with the modeling language macros
# that are expanded by venture.sivm.macro (first).  One difference:
# this code does not conserve expression indexes the way the sivm
# macro expander does.  This is probably a bug.

import venture.value.dicts as v

def quasiquote(exp):
  import collections
  # TODO Nested quasiquotation
  def quotify(exp, to_quote):
    if to_quote:
      return v.quote(exp)
    else:
      return exp
  def quasiquoterecur(exp):
    """Returns either (exp, True), if quasiquotation reduces to quotation on
exp, or (exp', False), where exp' is a directly evaluable expression that
will produce the term that the quasiquotation body exp means."""
    if hasattr(exp, "__iter__") and not isinstance(exp, collections.Mapping):
      if len(exp) > 0 and isinstance(exp[0], collections.Mapping) and exp[0]["type"] == "symbol" and exp[0]["value"] == "unquote":
        return (exp[1], False)
      else:
        answers = [quasiquoterecur(expi) for expi in exp]
        if all([ans[1] for ans in answers]):
          return (exp, True)
        else:
          return ([v.sym("array")] + [quotify(*ansi) for ansi in answers], False)
    else:
      return (exp, True)
  return quotify(*quasiquoterecur(exp))

def symbol_prepend(prefix, symbol):
  if isinstance(symbol, basestring):
    return prefix + symbol
  else:
    return v.symbol(prefix + symbol["value"])

def macroexpand_inference(program):
  if type(program) is list and len(program) == 0:
    return program
  elif type(program) is list and type(program[0]) is dict and program[0]["value"] in macros:
    return macros[program[0]["value"]](program)
  elif type(program) is list: return [macroexpand_inference(p) for p in program]
  else: return program

macro_list = []
macros = {}

def register_macro(name, func, desc=None):
  macro_list.append((name, func, desc))
  macros[name] = func

def cycle_macro(program):
  assert len(program) == 3
  subkernels = macroexpand_inference(program[1])
  transitions = macroexpand_inference(program[2])
  return [v.sym("_cycle"), [v.sym("list")] + subkernels, transitions]
register_macro("cycle", cycle_macro, """\
- `(cycle (<kernel> ...) <transitions>)`: Run a cycle kernel.

  Execute each of the given subkernels in order.

  The `transitions` argument specifies how many times to do this.
""")
