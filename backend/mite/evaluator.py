from venture.exception import VentureException
from venture.lite.exception import VentureError
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.node import isRequestNode
import venture.lite.exp as e

def evalFamily(trace, address, exp, env):
  weight = 0
  if e.isVariable(exp):
    try:
      sourceNode = env.findSymbol(exp)
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), \
        None, info[2]
    # weight = regen(trace, sourceNode, scaffold,
    #                shouldRestore, omegaDB, gradients)
    return (weight, trace.createLookupNode(address, sourceNode))
  elif e.isSelfEvaluating(exp):
    return (0, trace.createConstantNode(address, exp))
  elif e.isQuotation(exp):
    return (0, trace.createConstantNode(address, e.textOfQuotation(exp)))
  else:
    raise VentureException("stub for procedure application")

def unevalFamily(trace, node):
  weight = 0
  if isConstantNode(node): pass
  elif isLookupNode(node):
    assert len(trace.parentsAt(node)) == 1
    trace.disconnectLookup(node)
    trace.setValueAt(node, None)
    # weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  else:
    raise VentureException("stub for procedure application")
  return weight
