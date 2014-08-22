import numbers
import exp as e
from node import ConstantNode, LookupNode, RequestNode, OutputNode
from sp import VentureSPRecord
from psp import NullRequestPSP, PSP
from value import SPRef
from lkernel import VariationalLKernel
from scope import isScopeIncludeOutputPSP
from consistency import assertTorus, assertTrace
from exception import VentureError
from venture.exception import VentureException

def regenAndAttach(trace,scaffold,shouldRestore,omegaDB,gradients):
  assertTorus(scaffold)
  assert len(scaffold.border) == 1
  ans = regenAndAttachAtBorder(trace, scaffold.border[0], scaffold, shouldRestore, omegaDB, gradients)
  assertTrace(trace, scaffold)
  return ans

def regenAndAttachAtBorder(trace,border,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  constraintsToPropagate = {}
  for node in border:
#    print "regenAndAttach...",node
    if scaffold.isAbsorbing(node):
      weight += attach(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    else:
      weight += regen(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if node.isObservation:
        appNode = trace.getConstrainableNode(node)
        weight += constrain(trace,appNode,node.observedValue)
        constraintsToPropagate[appNode] = node.observedValue
  for node,value in constraintsToPropagate.iteritems():
    for child in trace.childrenAt(node):
      propagateConstraint(trace,child,value)

  assert isinstance(weight, numbers.Number)
  return weight

def constrain(trace,node,value):
  psp,args = trace.pspAt(node),trace.argsAt(node)
  psp.unincorporate(trace.valueAt(node),args)
  weight = psp.logDensity(value,args)
  trace.setValueAt(node,value)
  psp.incorporate(value,args)
  trace.registerConstrainedChoice(node)
  assert isinstance(weight, numbers.Number)
  return weight

def propagateConstraint(trace,node,value):
  if isinstance(node,LookupNode): trace.setValueAt(node,value)
  elif isinstance(node,RequestNode):
    if not isinstance(trace.pspAt(node),NullRequestPSP):
      raise Exception("Cannot make requests downstream of a node that gets constrained during regen")
  else:
    # TODO there may be more cases to ban here.
    # e.g. certain kinds of deterministic coupling through mutation.
    assert isinstance(node,OutputNode)
    if trace.pspAt(node).isRandom():
      raise Exception("Cannot make random choices downstream of a node that gets constrained during regen")
    # TODO Is it necessary to unincorporate and incorporate here?  If
    # not, why not?
    trace.setValueAt(node,trace.pspAt(node).simulate(trace.argsAt(node)))
  for child in trace.childrenAt(node): propagateConstraint(trace,child,value)

def attach(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
  psp,args,gvalue = trace.pspAt(node),trace.argsAt(node),trace.groundValueAt(node)
  weight += psp.logDensity(gvalue,args)
  psp.incorporate(gvalue,args)
  assert isinstance(weight, numbers.Number)
  return weight

def regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in trace.definiteParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  for parent in trace.esrParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def regenESRParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in trace.esrParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def regen(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  if scaffold.isResampling(node):
    if trace.regenCountAt(scaffold,node) == 0:
      weight += regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if isinstance(node,LookupNode):
        trace.setValueAt(node, trace.valueAt(node.sourceNode))
      else: 
        weight += applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients)
        if isinstance(node,RequestNode): weight += evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    trace.incRegenCountAt(scaffold,node)

  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += regen(trace,value.makerNode,scaffold,shouldRestore,omegaDB,gradients)

  assert isinstance(weight, numbers.Number)
  return weight

def evalFamily(trace,address,exp,env,scaffold,shouldRestore,omegaDB,gradients):
  if e.isVariable(exp):
    try:
      sourceNode = env.findSymbol(exp)
    except VentureError as err:
      raise VentureException("runtime", err.message, address=address)
    weight = regen(trace,sourceNode,scaffold,shouldRestore,omegaDB,gradients)
    return (weight,trace.createLookupNode(address,sourceNode))
  elif e.isSelfEvaluating(exp): return (0,trace.createConstantNode(address,exp))
  elif e.isQuotation(exp): return (0,trace.createConstantNode(address,e.textOfQuotation(exp)))
  else:
    weight = 0
    nodes = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      w, n = evalFamily(trace,addr,subexp,env,scaffold,shouldRestore,omegaDB,gradients)
      weight += w
      nodes.append(n)

    (requestNode,outputNode) = trace.createApplicationNodes(address,nodes[0],nodes[1:],env)
    try:
      weight += apply(trace,requestNode,outputNode,scaffold,shouldRestore,omegaDB,gradients)
    except VentureError as err:
      raise VentureException("runtime", err.message, address=address)
    assert isinstance(weight, numbers.Number)
    return weight,outputNode

def apply(trace,requestNode,outputNode,scaffold,shouldRestore,omegaDB,gradients):
  weight = applyPSP(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  assert len(trace.esrParentsAt(outputNode)) == len(trace.valueAt(requestNode).esrs)
  weight += regenESRParents(trace,outputNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def processMadeSP(trace,node,isAAA):
  spRecord = trace.valueAt(node)
  assert isinstance(spRecord,VentureSPRecord)
  trace.setMadeSPRecordAt(node,spRecord)
  if isAAA:
    trace.discardAAAMadeSPAuxAt(node)
  if spRecord.sp.hasAEKernel(): trace.registerAEKernel(node)
  trace.setValueAt(node,SPRef(node))

def applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  psp,args = trace.pspAt(node),trace.argsAt(node)
  assert isinstance(psp, PSP)

  if omegaDB.hasValueFor(node): oldValue = omegaDB.getValue(node)
  else: oldValue = None

  if scaffold.hasLKernel(node):
    k = scaffold.getLKernel(node)
    newValue = k.simulate(trace,oldValue,args) if not shouldRestore else oldValue
    weight += k.weight(trace,newValue,oldValue,args)
    assert isinstance(weight, numbers.Number)
    if isinstance(k,VariationalLKernel): 
      gradients[node] = k.gradientOfLogDensity(newValue,args)
  else: 
    # if we simulate from the prior, the weight is 0
    newValue = psp.simulate(args) if not shouldRestore else oldValue

  trace.setValueAt(node,newValue)
  psp.incorporate(newValue,args)

  if isinstance(newValue,VentureSPRecord): processMadeSP(trace,node,scaffold.isAAA(node))
  if psp.isRandom(): trace.registerRandomChoice(node)
  if isScopeIncludeOutputPSP(psp):
    scope,block = [trace.valueAt(n) for n in node.operandNodes[0:2]]
    blockNode = node.operandNodes[2]
    trace.registerRandomChoiceInScope(scope,block,blockNode)
  assert isinstance(weight, numbers.Number)
  return weight

def evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  assert isinstance(node,RequestNode)
  weight = 0
  request = trace.valueAt(node)

  # first evaluate exposed simulation requests (ESRs)
  for esr in request.esrs:
    if not trace.containsSPFamilyAt(node,esr.id):
      if shouldRestore and omegaDB.hasESRParent(trace.spAt(node),esr.id):
        esrParent = omegaDB.getESRParent(trace.spAt(node),esr.id)
        weight += restore(trace,esrParent,scaffold,omegaDB,gradients)
      else:
        address = node.address.request(esr.addr)
        (w,esrParent) = evalFamily(trace,address,esr.exp,esr.env,scaffold,shouldRestore,omegaDB,gradients)
        weight += w
      trace.registerFamilyAt(node,esr.id,esrParent)

    esrParent = trace.spFamilyAt(node,esr.id)
    trace.addESREdge(esrParent,node.outputNode)

  # next evaluate latent simulation requests (LSRs)
  for lsr in request.lsrs:
    if omegaDB.hasLatentDB(trace.spAt(node)): latentDB = omegaDB.getLatentDB(trace.spAt(node))
    else: latentDB = None
    weight += trace.spAt(node).simulateLatents(trace.spauxAt(node),lsr,shouldRestore,latentDB)
  
  assert isinstance(weight, numbers.Number)
  return weight

def restore(trace,node,scaffold,omegaDB,gradients):
  if isinstance(node,ConstantNode): return 0
  if isinstance(node,LookupNode):
    weight = regenParents(trace,node,scaffold,True,omegaDB,gradients)
    trace.reconnectLookup(node)
    trace.setValueAt(node,trace.valueAt(node.sourceNode))
    assert isinstance(weight, numbers.Number)
    return weight
  else: # node is output node
    assert isinstance(node,OutputNode)
    weight = restore(trace,node.operatorNode,scaffold,omegaDB,gradients)
    for operandNode in node.operandNodes: weight += restore(trace,operandNode,scaffold,omegaDB,gradients)
    weight += apply(trace,node.requestNode,node,scaffold,True,omegaDB,gradients)
    assert isinstance(weight, numbers.Number)
    return weight
