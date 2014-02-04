from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from omegadb import OmegaDB
from psp import ESRRefOutputPSP
from spref import SPRef
from scope import ScopeIncludeOutputPSP

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
  psp,args,value = trace.pspAt(node),trace.argsAt(node),trace.valueAt(node)
  trace.unregisterConstrainedChoice(node)
  psp.unincorporate(value,args)
  weight = psp.logDensity(value,args)
  psp.incorporate(value,args)
  return weight

def detach(trace,node,scaffold,omegaDB):
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  psp,args,gvalue = trace.pspAt(node),trace.argsAt(node),trace.groundValueAt(node)  
  psp.unincorporate(gvalue,args)
  weight = psp.logDensity(gvalue,args)
  weight += extractParents(trace,node,scaffold,omegaDB)
  return weight

def extractParents(trace,node,scaffold,omegaDB):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)): weight += extract(trace,parent,scaffold,omegaDB)
  for parent in reversed(trace.definiteParentsAt(node)): weight += extract(trace,parent,scaffold,omegaDB)    
  return weight

def extractESRParents(trace,node,scaffold,omegaDB):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)): weight += extract(trace,parent,scaffold,omegaDB)
  return weight

def extract(trace,node,scaffold,omegaDB):
  weight = 0
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += extract(trace,value.makerNode,scaffold,omegaDB)

  if scaffold.isResampling(node):
    trace.decRegenCountAt(scaffold,node)
    assert trace.regenCountAt(scaffold,node) >= 0
    if trace.regenCountAt(scaffold,node) == 0:
      if isinstance(node,ApplicationNode): 
        if isinstance(node,RequestNode): weight += unevalRequests(trace,node,scaffold,omegaDB)
        weight += unapplyPSP(trace,node,scaffold,omegaDB)
      else: 
        trace.setValueAt(node,None)
      weight += extractParents(trace,node,scaffold,omegaDB)

  return weight

def unevalFamily(trace,node,scaffold,omegaDB):
  weight = 0
  if isinstance(node,ConstantNode): pass
  elif isinstance(node,LookupNode):
    trace.disconnectLookup(node)
    trace.setValueAt(node,None)
    weight += extractParents(trace,node,scaffold,omegaDB)
  else:
    assert isinstance(node,OutputNode)
    weight += unapply(trace,node,scaffold,omegaDB)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace,operandNode,scaffold,omegaDB)
    weight += unevalFamily(trace,node.operatorNode,scaffold,omegaDB)
  return weight

def unapply(trace,node,scaffold,omegaDB):
  weight = unapplyPSP(trace,node,scaffold,omegaDB)
  weight += extractESRParents(trace,node,scaffold,omegaDB)
  weight += unevalRequests(trace,node.requestNode,scaffold,omegaDB)
  weight += unapplyPSP(trace,node.requestNode,scaffold,omegaDB)
  return weight

def teardownMadeSP(trace,node,isAAA):
  sp = trace.madeSPAt(node)
  trace.setValueAt(node,sp)
  trace.setMadeSPAt(node,None)
  if not isAAA: 
    if sp.hasAEKernel(): trace.unregisterAEKernel(node)
    trace.setMadeSPAuxAt(node,None)
    trace.clearMadeSPFamiliesAt(node)

def unapplyPSP(trace,node,scaffold,omegaDB):
  psp,args = trace.pspAt(node),trace.argsAt(node)
  if isinstance(psp,ScopeIncludeOutputPSP):
    scope,block = [n.value for n in node.operandNodes[0:2]]
    blockNode = node.operandNodes[2]
    trace.unregisterRandomChoiceInScope(scope,block,blockNode)
  if psp.isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(trace.valueAt(node),SPRef) and trace.valueAt(node).makerNode == node:
    teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  psp.unincorporate(trace.valueAt(node),args)
  if scaffold.hasLKernel(node): 
    weight += scaffold.getLKernel(node).reverseWeight(trace,trace.valueAt(node),args)
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
    if trace.numRequestsAt(esrParent) == 0:
      trace.unregisterFamilyAt(node,esr.id)
      omegaDB.registerSPFamily(trace.spAt(node),esr.id,esrParent)
      weight += unevalFamily(trace,esrParent,scaffold,omegaDB)

  return weight
