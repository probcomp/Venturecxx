from ..lite import exp as e
from ..lite.exception import VentureError
from venture.exception import VentureException
from ..lite.inference_sps import VentureNestedRiplMethodError # TODO Ugh.

from ..lite.psp import PSP

def eval(address, exp, env):
  if e.isVariable(exp):
    try:
      value = env.findSymbol(exp)
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), None, info[2]
    return value
  elif e.isSelfEvaluating(exp): return exp
  elif e.isQuotation(exp): return e.textOfQuotation(exp)
  else:
    vals = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      v = eval(addr,subexp,env)
      vals.append(v)

    try:
      val = apply(address, vals, env)
    except VentureNestedRiplMethodError as err:
      # This is a hack to allow errors raised by inference SP actions
      # that are ripl actions to blame the address of the maker of the
      # action rather than the current address, which is the
      # application of that action (which is where the mistake is
      # detected).
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=err.addr, cause=err), None, info[2]
    except VentureException:
      raise # Avoid rewrapping with the below
    except Exception as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
    return val

def apply(address, vals, env):
  sp = vals[0]
  inputs = vals[1:]
  requests = applyPSP(sp.requestPSP, inputs, env, [])
  more = [evalRequest(address, r) for r in requests]
  # TODO Do I need to do anything about LSRs?
  return applyPSP(sp.outputPSP, inputs, env, more)

def applyPSP(psp, inputs, env, esr_vals):
  args = inputs  # Actually trace.argsAt(node)
  assert isinstance(psp, PSP)
  val = psp.simulate(args)
  psp.incorporate(val, args)
  # At this point, Lite converts any SPRecord values to SPRefs
  return val

def evalRequest(address, r):
  # TODO Maintain mem tables by request id
  return eval(address, r.exp, r.env)
