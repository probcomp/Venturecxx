from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from omegadb import OmegaDB
from value import SPRef
from scope import isScopeIncludeOutputPSP
from sp import VentureSPRecord
from consistency import assertTorus, assertTrace

def detachAndExtract(trace, scaffold, compute_gradient = False):
  assertTrace(trace, scaffold)
  assert len(scaffold.border) == 1
  ans = detachAndExtractAtBorder(trace, scaffold.border[0], scaffold, compute_gradient=compute_gradient)
  assertTorus(scaffold)
  return ans

def detachAndExtractAtBorder(trace, border, scaffold, compute_gradient = False):
  """Returns the weight and an OmegaDB.  The OmegaDB contains
  sufficient information to restore the trace, and, if
  compute_gradient is True, to determine the partial derivative of
  the weight with respect to the value at each node.  The latter is
  computed by one level of reverse-mode AD, with the underlying trace
  serving as tape."""
  weight = 0
  omegaDB = OmegaDB()
  for node in reversed(border):
    if scaffold.isAbsorbing(node):
      weight += detach(trace, node, scaffold, omegaDB, compute_gradient)
    else:
      if node.isObservation: weight += unconstrain(trace,trace.getConstrainableNode(node))
      weight += extract(trace,node,scaffold,omegaDB, compute_gradient)
  return weight,omegaDB

def unconstrain(trace,node):
  psp,args,value = trace.pspAt(node),trace.argsAt(node),trace.valueAt(node)
  trace.unregisterConstrainedChoice(node)
  psp.unincorporate(value,args)
  weight = psp.logDensity(value,args)
  psp.incorporate(value,args)
  return weight

def detach(trace, node, scaffold, omegaDB, compute_gradient = False):
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  psp,args,gvalue = trace.pspAt(node),trace.argsAt(node),trace.groundValueAt(node)  
  psp.unincorporate(gvalue,args)
  weight = psp.logDensity(gvalue,args)
  if compute_gradient:
    # Ignore the partial derivative of the value because the value is fixed
    (_, grad) = psp.gradientOfLogDensity(gvalue, args)
    omegaDB.addPartials(args.operandNodes + trace.esrParentsAt(node), grad)
  weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  return weight

def extractParents(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  for parent in reversed(trace.definiteParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  return weight

def extractESRParents(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  return weight

def extract(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += extract(trace, value.makerNode, scaffold, omegaDB, compute_gradient)

  if scaffold.isResampling(node):
    trace.decRegenCountAt(scaffold,node)
    assert trace.regenCountAt(scaffold,node) >= 0
    if trace.regenCountAt(scaffold,node) == 0:
      if isinstance(node,ApplicationNode):
        if isinstance(node,RequestNode):
          weight += unevalRequests(trace, node, scaffold, omegaDB, compute_gradient)
        weight += unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient)
      else: 
        trace.setValueAt(node,None)
        assert isinstance(node, LookupNode) or isinstance(node, ConstantNode)
        assert len(trace.parentsAt(node)) <= 1
        if compute_gradient:
          for p in trace.parentsAt(node):
            omegaDB.addPartial(p, omegaDB.getPartial(node)) # d/dx is 1 for a lookup node
      weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)

  return weight

def unevalFamily(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  if isinstance(node,ConstantNode): pass
  elif isinstance(node,LookupNode):
    assert len(trace.parentsAt(node)) == 1
    if compute_gradient:
      for p in trace.parentsAt(node):
        omegaDB.addPartial(p, omegaDB.getPartial(node)) # d/dx is 1 for a lookup node
    trace.disconnectLookup(node)
    trace.setValueAt(node,None)
    weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  else:
    assert isinstance(node,OutputNode)
    weight += unapply(trace, node, scaffold, omegaDB, compute_gradient)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace, operandNode, scaffold, omegaDB, compute_gradient)
    weight += unevalFamily(trace, node.operatorNode, scaffold, omegaDB, compute_gradient)
  return weight

def unapply(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient)
  weight += extractESRParents(trace, node, scaffold, omegaDB, compute_gradient)
  weight += unevalRequests(trace, node.requestNode, scaffold, omegaDB, compute_gradient)
  weight += unapplyPSP(trace, node.requestNode, scaffold, omegaDB, compute_gradient)
  return weight

def teardownMadeSP(trace,node,isAAA):
  spRecord = trace.madeSPRecordAt(node)
  assert isinstance(spRecord,VentureSPRecord)
  trace.setValueAt(node,spRecord)
  if spRecord.sp.hasAEKernel(): trace.unregisterAEKernel(node)
  if isAAA:
    trace.registerAAAMadeSPAuxAt(node,trace.madeSPAuxAt(node))
  trace.setMadeSPRecordAt(node,None)

def unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient = False):
  psp,args = trace.pspAt(node),trace.argsAt(node)
  if isScopeIncludeOutputPSP(psp):
    scope,block = [trace.valueAt(n) for n in node.operandNodes[0:2]]
    blockNode = node.operandNodes[2]
    trace.unregisterRandomChoiceInScope(scope,block,blockNode)
  if psp.isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(trace.valueAt(node),SPRef) and trace.valueAt(node).makerNode == node:
    teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  psp.unincorporate(trace.valueAt(node),args)
  if scaffold.hasLKernel(node):
    weight += scaffold.getLKernel(node).reverseWeight(trace,trace.valueAt(node),args)
    if compute_gradient:
      # TODO Should this take the whole args?  Should it take the esr parents into account?
      (partial, grad) = scaffold.getLKernel(node).gradientOfReverseWeight(trace, trace.valueAt(node), args)
      omegaDB.addPartial(node, partial)
      omegaDB.addPartials(args.operandNodes, grad)
  omegaDB.extractValue(node,trace.valueAt(node))

#  print "unapplyPSP",trace.valueAt(node)

  trace.setValueAt(node,None)
  if compute_gradient and any([scaffold.isResampling(p) or scaffold.isBrush(p) for p in trace.parentsAt(node)]):
    # Don't need to compute the simulation gradient if the parents are
    # not in the DRG or brush.
    grad = psp.gradientOfSimulate(args, omegaDB.getValue(node), omegaDB.getPartial(node))
    omegaDB.addPartials(args.operandNodes + trace.esrParentsAt(node), grad)

  return weight

def unevalRequests(trace, node, scaffold, omegaDB, compute_gradient = False):
  assert isinstance(node,RequestNode)
  weight = 0
  request = trace.valueAt(node)
  # TODO I may have the following AD bug: if a request constructs an
  # expression which contains an embedded constant, the constant node
  # will not propagate the partial wrt that constant; and even if it
  # did, I wouldn't know how to backpropagate that partial through the
  # expression generator to the args.
  if request.lsrs and not omegaDB.hasLatentDB(trace.spAt(node)):
    omegaDB.registerLatentDB(trace.spAt(node),trace.spAt(node).constructLatentDB())

  for lsr in reversed(request.lsrs):
    weight += trace.spAt(node).detachLatents(trace.spauxAt(node),lsr,omegaDB.getLatentDB(trace.spAt(node)))
    # TODO add gradient information for detached latents?

  for esr in reversed(request.esrs):
    esrParent = trace.popLastESRParent(node.outputNode)
    if trace.numRequestsAt(esrParent) == 0:
      trace.unregisterFamilyAt(node,esr.id)
      omegaDB.registerSPFamily(trace.spAt(node),esr.id,esrParent)
      weight += unevalFamily(trace, esrParent, scaffold, omegaDB, compute_gradient)

  return weight
