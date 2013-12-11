def unevalFamily(trace,node,scaffold,omegaDB):
  weight = 0
  if node.isConstantNode(): pass
  elif node.isLookupNode():
    node.disconnectLookup(node)
    weight += extract(node.sourceNode(),scaffold,omegaDB)
  else:
    weight += unapply(node,scaffold,omegaDB)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace,operandNode,scaffold,omegaDB)
    weight += unevalFamily(trace,node.operatorNode(),scaffold,omegaDB)
  return weight

def unapply(trace,node,scaffold,omegaDB):
  weight = unapplyPSP(node,scaffold,omegaDB)
  weight += unevalRequests(trace,node.requestNode(),scaffold,omegaDB)
  weight += unapplyPSP(node.requestNode(),scaffold,omegaDB)
  return weight

def teardownMadeSP(trace,node,isAAA):
  sp = node.madeSP
  node.value = sp
  node.madeSP = None
  if not isAAA: 
    if sp.hasAEKernel(): trace.unregisterAEKernel(node)
    node.madeSPAux = None

def unapplyPSP(node,scaffold,omegaDB):
  if node.psp().isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(node.value,SPRef) and node.value.makerNode == node: teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  node.psp().remove(node.value,node.args())
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
