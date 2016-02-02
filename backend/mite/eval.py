from venture.lite.regen import *
from venture.lite.detach import *

from venture.mite.sp import *

def evalFamily(trace, address, exp, env, constraint=None):
  if e.isVariable(exp):
    try:
      sourceNode = env.findSymbol(exp)
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), None, info[2]
    assert constraint is None, "Cannot constrain" # TODO does it make sense to evaluate a variable lookup subject to a constraint? does this turn the below regen into an absorb? what if multiple lookups of the same variable are constrained to different values? can we detect this as a case of source having already been regenned?
    weight = 0 # TODO regen source node?
    return (weight, trace.createLookupNode(address, sourceNode))
  elif e.isSelfEvaluating(exp):
    assert constraint is None, "Cannot constrain"
    return (0, trace.createConstantNode(address,exp))
  elif e.isQuotation(exp): return (0, trace.createConstantNode(address,e.textOfQuotation(exp)))
  else: # SP application
    weight = 0
    nodes = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      w, n = evalFamily(trace, addr, subexp, env)
      weight += w
      nodes.append(n)

    outputNode = trace.createOutputNode(address, nodes[0], nodes[1:], env)
    try:
      weight += apply(trace, outputNode, constraint)
    except VentureException:
      raise # Avoid rewrapping with the below
    except Exception as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
    assert isinstance(weight, numbers.Number)
    return (weight, outputNode)

def evalRequests(trace, node):
  weight = 0
  request = trace.valueAt(node)

  # first evaluate exposed simulation requests (ESRs)
  for esr in request.esrs:
    if not trace.containsSPFamilyAt(node, esr.id):
      address = node.address.request(esr.addr)
      (w, esrParent) = evalFamily(trace, address, esr.exp, esr.env, esr.constraint)
      weight += w
      if trace.containsSPFamilyAt(node,esr.id):
        # evalFamily already registered a family with this id for the
        # operator being applied here, which means a recursive call to
        # the operator issued a request for the same id.  Currently,
        # the only way for that it happen is for a recursive memmed
        # function to call itself with the same arguments.
        raise VentureException("evaluation", "Recursive mem argument loop detected.", address = node.address)
      trace.registerFamilyAt(node,esr.id,esrParent)

    esrParent = trace.spFamilyAt(node, esr.id)
    trace.addESREdge(esrParent, node.outputNode)

  # TODO: next evaluate latent simulation requests (LSRs)

  assert isinstance(weight, numbers.Number)
  return weight

def apply(trace, node, constraint):
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  newValue, weight = sp.apply(args, constraint)
  while isinstance(newValue, tuple) and isinstance(newValue[0], Request):
    requestNode = trace.createRequestNode(
      node.address, node.operatorNode, node.operandNodes, node, node.env)
    request, cont, uncont = newValue
    trace.setValueAt(requestNode, request)
    requestNode.cont = cont # TODO stick this someplace better
    requestNode.uncont = uncont
    weight += evalRequests(trace, requestNode)
    newValue, newWeight = cont(request, args, constraint)
    weight += newWeight
  trace.setValueAt(node, newValue)
  if isinstance(newValue, VentureSPRecord):
    processMadeSP(trace, node, False)
  return weight

def unapply(trace, node, constraint):
  # TODO: look up the request nodes in the scaffold to determine
  # whether to unapply them, or keep them and resume from their
  # continuation when reapplied
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  oldValue = trace.valueAt(node)
  if isinstance(oldValue, VentureSPRecord):
    teardownMadeSP(trace, node, False)
  weight = sp.unapply(oldValue, args, constraint)
  while node.requestNode:
    requestNode = node.requestNode.pop()
    weight += unevalRequests(trace, requestNode)
    request = trace.valueAt(requestNode)
    weight += requestNode.uncont(request, args, constraint)
    trace.removeRequestNode(requestNode)
  trace.setValueAt(node, None)
  return weight

def constrain(trace, node, constraint):
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  oldValue = trace.valueAt(node)
  rhoWeight = sp.unapply(oldValue, args, None)
  newValue, xiWeight = sp.apply(args, constraint)
  trace.setValueAt(node, newValue)
  return rhoWeight + xiWeight

def unconstrain(trace, node, constraint):
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  oldValue = trace.valueAt(node)
  rhoWeight = sp.unapply(oldValue, args, constraint)
  newValue, xiWeight = sp.apply(args, None)
  trace.setValueAt(node, newValue)
  return rhoWeight + xiWeight

def unevalFamily(trace, node, constraint=None):
  weight = 0
  if isConstantNode(node): pass
  elif isLookupNode(node):
    assert len(trace.parentsAt(node)) == 1
    trace.disconnectLookup(node)
    trace.setValueAt(node,None)
    # TODO detach source node
  else:
    assert isOutputNode(node)
    weight += unapply(trace, node, constraint)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace, operandNode)
    weight += unevalFamily(trace, node.operatorNode)
  return weight

def unevalRequests(trace, node):
  assert isRequestNode(node)
  weight = 0
  request = trace.valueAt(node)

  # TODO LSRs

  for esr in reversed(request.esrs):
    esrParent = trace.popLastESRParent(node.outputNode)
    if trace.numRequestsAt(esrParent) == 0:
      trace.unregisterFamilyAt(node,esr.id)
      weight += unevalFamily(trace, esrParent, esr.constraint)

  return weight

