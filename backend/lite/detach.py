from node import LookupNode, ApplicationNode, RequestNode, OutputNode
from omegadb import OmegaDB
from psp import ESRRefOutputPSP
from sp import SP
from spref import SPRef

def unconstrain(trace,node):
  if isinstance(node,LookupNode): return unconstrain(trace,node.sourceNode)
  if isinstance(node.psp(),ESRRefOutputPSP): return unconstrain(trace,node.esrParents[0])

  if node.psp().isRandom(): trace.registerRandomChoice(node)
  node.psp().unincorporate(node.value,node.args())
  weight = node.psp().logDensity(value,node.args())
  node.psp().incorporateOutput(node.value,node.args())
  return weight

def detachAndExtract(trace,border,scaffold):
  weight = 0
  omegaDB = OmegaDB()
  for node in reversed(border):
    if scaffold.isAbsorbing(node):
      weight += detach(trace,node,scaffold,omegaDB)
    else:
      if node.isConstrained: weight += unconstrain(node)
      weight += extract(trace,node,scaffold,omegaDB)
  return weight,omegaDB
  
def extractParents(trace,node,scaffold,omegaDB):
  weight = 0
  for parent in reversed(node.parents()): weight += extract(trace,node,scaffold,omegaDB)
  return weight

def detach(trace,node,scaffold,omegaDB):
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  node.psp().unincorporate(node.groundValue(),node.args())
  weight = node.psp().logDensity(node.groundValue(),node.args())
  weight += extractParents(trace,node,scaffold,omegaDB)
  return weight

def extract(trace,node,scaffold,omegaDB):
  weight = 0
  if isinstance(node.value,SPRef) and node.value.makerNode != node and scaffold.isAAA(node.value.makerNode):
    weight += extract(trace,node.value.makerNode,scaffold,omegaDB)

  if scaffold.isResampling(node):
    scaffold.decrementRegenCount(node)
    if scaffold.regenCount(node) == 0:
      if isinstance(node,ApplicationNode): 
        if isinstance(node,RequestNode): weight += unevalRequests(trace,node,scaffold,omegaDB)
        weight += unapplyPSP(trace,node,scaffold,omegaDB)
      weight += extractParents(trace,node,scaffold,omegaDB)

  return weight

def unevalFamily(trace,node,scaffold,omegaDB):
  weight = 0
  if isinstance(node,ConstantNode): pass
  elif isinstance(node,LookupNode):
    node.disconnectLookup(node)
    weight += extract(node.sourceNode,scaffold,omegaDB)
  else:
    weight += unapply(trace,node,scaffold,omegaDB)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace,operandNode,scaffold,omegaDB)
    weight += unevalFamily(trace,node.operatorNode(),scaffold,omegaDB)
  return weight

def unapply(trace,node,scaffold,omegaDB):
  weight = unapplyPSP(trace,node,scaffold,omegaDB)
  weight += unevalRequests(trace,node.requestNode,scaffold,omegaDB)
  weight += unapplyPSP(trace,node.requestNode,scaffold,omegaDB)
  return weight

def teardownMadeSP(trace,node,isAAA):
  sp = node.madeSP
  node.value = sp
  node.madeSP = None
  if not isAAA: 
    if sp.hasAEKernel(): trace.unregisterAEKernel(node)
    node.madeSPAux = None

def unapplyPSP(trace,node,scaffold,omegaDB):
  print "unapplyPSP: " + str(node)

  if node.psp().isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(node.value,SPRef) and node.value.makerNode == node: teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  node.psp().unincorporate(node.value,node.args())
  if scaffold.hasKernelFor(node): 
    weight += scaffold.kernel(node).reverseWeight(node.value,node.args())
  omegaDB.extractValue(node,node.value)
  return weight

def unevalRequests(trace,requestNode,scaffold,omegaDB):
  weight = 0
  request = requestNode.value
  if request.lsrs and not omegaDB.hasLatentDB(node.sp()):
    omegaDB.registerLatentDB(node.sp(),node.sp().constructLatentDB())

  for lsr in reversed(request.lsrs):
    weight += node.sp().detachLatents(node.spaux(),lsr,omegaDB.getLatentDB(node.sp()))

  for esr in reversed(request.esrs):
    esrParent = trace.popLastESRParent(node.outputNode)
    if esr.block: trace.unregisterBlock(esr.block,esr.subblock,esrParent)
    if esrParent.numRequests == 0:
      node.spaux().unregisterFamily(esr.id)
      omegaDB.registerSPFamily(node.sp(),esr.id,esrParent)
      weight += unevalFamily(trace,node,scaffold,omegaDB)
    else: weight += extract(trace,esrParent,scaffold,omegaDB)

  return weight
