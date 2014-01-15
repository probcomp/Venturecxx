from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from omegadb import OmegaDB
from psp import ESRRefOutputPSP
from sp import SP
from spref import SPRef


def detachAndExtract(trace,border,scaffold):
  weight = 0
  omegaDB = OmegaDB()
  for node in reversed(border):
    if scaffold.isAbsorbing(node):
      weight += detach(trace,node,scaffold,omegaDB)
    else:
      if node.isObservation: weight += unconstrain(trace,node)
      weight += extract(trace,node,scaffold,omegaDB)
  return weight,omegaDB

def unconstrain(trace,node):
  if isinstance(node,LookupNode): return unconstrain(trace,node.sourceNode)
  assert isinstance(node,OutputNode)
  if isinstance(trace.pspAt(node),ESRRefOutputPSP): return unconstrain(trace,trace.esrParentsAt(node)[0])

  trace.unregisterConstrainedChoice(node)
  trace.unincorporateAt(node)
  weight = trace.logDensityAt(node,trace.valueAt(node))
  trace.incorporateAt(node)
  return weight

def detach(trace,node,scaffold,omegaDB):
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  trace.unincorporateAt(node)
  weight = trace.logDensityAt(node,trace.groundValueAt(node))
  weight += extractParents(trace,node,scaffold,omegaDB)
  return weight

def extractParents(trace,node,scaffold,omegaDB):
  weight = 0
  for parent in reversed(trace.parentsAt(node)): weight += extract(trace,parent,scaffold,omegaDB)
  return weight

def extract(trace,node,scaffold,omegaDB):
  weight = 0
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += extract(trace,value.makerNode,scaffold,omegaDB)

  if scaffold.isResampling(node):
    scaffold.decrementRegenCount(node)
    assert scaffold.getRegenCount(node) >= 0
    if scaffold.getRegenCount(node) == 0:
      if isinstance(node,ApplicationNode): 
        if isinstance(node,RequestNode): weight += unevalRequests(trace,node,scaffold,omegaDB)
        weight += unapplyPSP(trace,node,scaffold,omegaDB)
      weight += extractParents(trace,node,scaffold,omegaDB)

  return weight

def unevalFamily(trace,node,scaffold,omegaDB):
  weight = 0
  if isinstance(node,ConstantNode): pass
  elif isinstance(node,LookupNode):
    trace.disconnectLookup(node)
    weight += extract(trace,node.sourceNode,scaffold,omegaDB)
  else:
    assert isinstance(node,OutputNode)
    weight += unapply(trace,node,scaffold,omegaDB)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace,operandNode,scaffold,omegaDB)
    weight += unevalFamily(trace,node.operatorNode,scaffold,omegaDB)
  return weight

def unapply(trace,node,scaffold,omegaDB):
  weight = unapplyPSP(trace,node,scaffold,omegaDB)
  weight += unevalRequests(trace,node.requestNode,scaffold,omegaDB)
  weight += unapplyPSP(trace,node.requestNode,scaffold,omegaDB)
  return weight

def teardownMadeSP(trace,node,isAAA):
  sp = trace.madeSPAt(node)
  trace.setValueAt(node,sp)
  trace.setMadeSPAt(node,None)
  if not isAAA: 
    if sp.hasAEKernel(): trace.unregisterAEKernel(node)
    trace.setMadeSPAux(node,None)

def unapplyPSP(trace,node,scaffold,omegaDB):

  if trace.pspAt(node).isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(trace.valueAt(node),SPRef) and trace.valueAt(node).makerNode == node:
    teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  trace.unincorporateAt(node)
  if scaffold.hasLKernel(node): 
    weight += scaffold.getLKernel(node).reverseWeight(trace,trace.valueAt(node),trace.argsAt(node))
  omegaDB.extractValue(node,trace.valueAt(node))

#  print "unapplyPSP",trace.valueAt(node)

  trace.setValueAt(node,None)

  return weight

def unevalRequests(trace,node,scaffold,omegaDB):
  assert isinstance(node,RequestNode)
  weight = 0
  request = trace.valueAt(node)
  if request.lsrs and not omegaDB.hasLatentDB(trace.spAt(node)):
    omegaDB.registerLatentDB(trace.spAt(node),trace.spAt(node).constructLatentDB())

  for lsr in reversed(request.lsrs):
    weight += trace.spAt(node).detachLatents(trace.spauxAt(node),lsr,omegaDB.getLatentDB(trace.spAt(node)))

  for esr in reversed(request.esrs):
    esrParent = trace.popLastESRParent(node.outputNode)
    if esr.block: trace.unregisterBlock(esr.block,esr.subblock,esrParent)
    if esrParent.numRequests == 0:
      trace.unregisterFamilyAt(node,esr.id)
      omegaDB.registerSPFamily(trace.spAt(node),esr.id,esrParent)
      weight += unevalFamily(trace,esrParent,scaffold,omegaDB)
    else: 
      weight += extract(trace,esrParent,scaffold,omegaDB)

  return weight
