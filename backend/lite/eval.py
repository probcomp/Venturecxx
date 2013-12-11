from exp import isVariable, isSelfEvaluating, isQuotation, textOfQuotation, getOperator, getOperands
from sp import SP
from spref import SPRef

def evalFamily(trace,exp,env,scaffold,omegaDB,gradients):
  weight = 0
  if isVariable(exp): return (0,trace.createLookupNode(env.findSymbol(exp)))
  elif isSelfEvaluating(exp): return (0,trace.createConstantNode(exp))
  elif isQuotation(exp): return (0,trace.createConstantNode(textOfQuotation(exp)))
  else:
    (weight,operatorNode) = evalFamily(trace,getOperator(exp),env,scaffold,omegaDB,gradients)
    operandNodes = []
    for operand in getOperands(exp):
      (w,operandNode) = evalFamily(trace,operand,env,scaffold,omegaDB,gradients)
      weight += w
      operandNodes.append(operandNode)

    (requestNode,outputNode) = trace.createApplicationNodes(operatorNode,operandNodes,env)
    weight += apply(trace,requestNode,outputNode,scaffold,False,omegaDB,gradients)
    return weight,outputNode

def apply(trace,requestNode,outputNode,scaffold,shouldRestore,omegaDB,gradients):
  weight = applyPSP(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,omegaDB,gradients)
  return weight

def processMadeSP(trace,node,isAAA):
  assert isinstance(node.value,SP)
  sp = node.value
  node.madeSP = sp
  node.value = SPRef(node)
  if not isAAA:
    node.madeSPAux = sp.constructSPAux()
    if sp.hasAEKernel(): trace.registerAEKernel(node)

def applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0;

  if omegaDB.hasValueFor(node): oldValue = omegaDB.getValue(node)
  else: oldValue = None

  if shouldRestore: newValue = oldValue
  elif scaffold.hasKernelFor(node):
    k = scaffold.getKernel(node)
    newValue = k.simulate(trace,oldValue,node.args())
    weight += k.weight(trace,newValue,oldValue,node.args())
    if gradients and k.isVariationalKernel(): 
      gradients[node] = k.gradientOfLogDensity(newValue,node.args()) 
  else: 
    # if we simulate from the prior, the weight is 0
    newValue = node.psp().simulate(node.args())

  node.psp().incorporate(newValue,node.args())
  node.value = newValue

  if isinstance(node.value,SP): processMadeSP(trace,node,scaffold.isAAA(node))
  if node.psp().isRandom(): trace.registerRandomChoice(node)
  return weight

def evalRequests(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0;
  request = requestNode.value

  # first evaluate exposed simulation requests (ESRs)
  for esr in request.esrs:
    if not requestNode.spaux().containsFamily(esr.id):
      if shouldRestore: weight += restore(omegaDB.getESRParent(requestNode.sp(),esr.id),scaffold,omegaDB)
      else:
        (w,esrParent) = evalFamily(trace,esr.exp,esr.env,scaffold,omegaDB,gradients)
        weight += w
        requestNode.spaux().registerFamily(esr.id,esrParent)
    else: 
      esrParent = requestNode.spaux().getFamily(esr.id)
      weight += regen(trace,esrParent,scaffold,shouldRestore,omegaDB)
    esrParent = requestNode.spaux().getFamily(esr.id)
    if esr.block: trace.registerBlock(esr.block,esr.subblock,esrParent)
    trace.addESREdge(esrParent,requestNode.outputNode)

  # next evaluate latent simulation requests (LSRs)
  for lsr in request.lsrs:
    weight += requestNode.sp().simulateLatents(requestNode.spaux(),lsr,shouldRestore,omegaDB.getLatentDB(requestNode.sp().makerNode()))
  
  return weight;

def restore(trace,node,scaffold,omegaDB,gradients):
  if node.isConstantNode(): pass
  if node.isLookupNode():
    regen(trace,node.sourceNode(),scaffold,True,omegaDB,gradients)
    node.value = node.sourceNode().value
    trace.reconnectLookup(node,node.sourceNode()) # awkward
  else: # node is output node
    weight = restore(trace,node.operatorNode(),scaffold,omegaDB,gradients)
    for operandNode in node.operandNodes(): weight += restore(trace,operandNode,scaffold,omegaDB,gradients)
    weight += apply(trace,node.requestNode(),node)
    return weight
