from exp import isVariable, isSelfEvaluating, isQuotation, textOfQuotation, getOperator, getOperands
from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from sp import SP
from psp import ESRRefOutputPSP
from spref import SPRef

def regenAndAttach(trace,border,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for node in border:
    if scaffold.isAbsorbing(node):
      weight += attach(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    else:
      weight += regen(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if node.isObservation: weight += constrain(trace,node,node.observedValue)
  return weight

def constrain(trace,node,value):
  if isinstance(node,LookupNode): return constrain(trace,node.sourceNode,value)
  assert isinstance(node,OutputNode)
  if isinstance(node.psp(),ESRRefOutputPSP): return constrain(trace,node.esrParents[0],value)
  node.psp().unincorporate(node.value,node.args())
  weight = node.psp().logDensity(value,node.args())
  node.value = value
  node.psp().incorporate(value,node.args())
  trace.unregisterRandomChoice(node)
  return weight

def attach(trace,node,scaffold,shouldRestore,omegaDB,gradients):
#  print "attach: " + str(node)
  weight = regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  weight += node.psp().logDensity(node.groundValue(),node.args())
  node.psp().incorporate(node.groundValue(),node.args())
  return weight

def regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in node.parents(): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  return weight


def regen(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  if scaffold.isResampling(node):
    if scaffold.regenCount(node) == 0:
      weight += regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if isinstance(node,LookupNode): node.value = node.sourceNode.value
      else: 
        weight += applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients)
        if isinstance(node,RequestNode): weight += evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    scaffold.incrementRegenCount(node)

  if isinstance(node.value,SPRef) and node.value.makerNode != node and scaffold.isAAA(node.value.makerNode):
    weight += regen(trace,node.value.makerNode,scaffold,shouldRestore,omegaDB,gradients)

  return weight

def evalFamily(trace,exp,env,scaffold,omegaDB,gradients):
  weight = 0
  if isVariable(exp): 
    sourceNode = env.findSymbol(exp)
    regen(trace,sourceNode,scaffold,False,omegaDB,gradients)
    return (0,trace.createLookupNode(sourceNode))
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
#  print "applyPSP: " + str(node)
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

def evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  assert isinstance(node,RequestNode)
  weight = 0;
  request = node.value

  # first evaluate exposed simulation requests (ESRs)
  for esr in request.esrs:
    if not node.spaux().containsFamily(esr.id):
      if shouldRestore: 
        esrParent = omegaDB.getESRParent(node.sp(),esr.id)
        weight += restore(trace,esrParent,scaffold,omegaDB,gradients)
      else:
        (w,esrParent) = evalFamily(trace,esr.exp,esr.env,scaffold,omegaDB,gradients)
        weight += w
      node.spaux().registerFamily(esr.id,esrParent)
    else: 
      esrParent = node.spaux().getFamily(esr.id)
      weight += regen(trace,esrParent,scaffold,shouldRestore,omegaDB,gradients)
    esrParent = node.spaux().getFamily(esr.id)
    if esr.block: trace.registerBlock(esr.block,esr.subblock,esrParent)
    trace.addESREdge(esrParent,node.outputNode)

  # next evaluate latent simulation requests (LSRs)
  for lsr in request.lsrs:
    if omegaDB.hasLatentDB(node.sp()): latentDB = omegaDB.getLatentDB(node.sp())
    else: latentDB = None
    weight += node.sp().simulateLatents(node.spaux(),lsr,shouldRestore,latentDB)
  
  return weight;

def restore(trace,node,scaffold,omegaDB,gradients):
  if isinstance(node,ConstantNode): return 0
  if isinstance(node,LookupNode):
    weight = regen(trace,node.sourceNode,scaffold,True,omegaDB,gradients)
    node.value = node.sourceNode.value
    trace.reconnectLookup(node) # awkward
    return weight
  else: # node is output node
    weight = restore(trace,node.operatorNode,scaffold,omegaDB,gradients)
    for operandNode in node.operandNodes: weight += restore(trace,operandNode,scaffold,omegaDB,gradients)
    weight += apply(trace,node.requestNode,node,scaffold,True,omegaDB,gradients)
    return weight
