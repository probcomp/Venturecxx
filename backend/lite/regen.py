def constrain(node,value):
  if node.isLookupNode(): return constrain(node.sourceNode(),value)
  if isinstance(node.psp(),ESRRefOutputPSP): return constrain(node.esrParents[0],value)
  node.psp().unincorporate(value,node.args())
  weight = node.psp().logDensity(value,node.args())
  node.setValue(value)
  node.psp().incorporateOutput(value,node.args())
  trace.unregisterRandomChoice(node)
  return weight

def regenAndAttach(trace,border,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for node in border:
    if scaffold.isAbsorbing(node):
      weight += attach(trace,scaffold,shouldRestore,omegaDB,gradients)
    else:
      weight += regen(trace,scaffold,shouldRestore,omegaDB,gradients)
      if node.isConstrained: weight += constrain(node,node.observedValue())
  return weight

def regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in node.parents(): weight += regen(trace,scaffold,shouldRestore,omegaDB,gradients)
  return weight

def attach(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  weight += node.psp().logDensity(node.groundValue(),node.args())
  node.psp().incorporate(node.groundValue(),node.args())
  return weight

def regen(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  if scaffold.isResampling(node):
    if scaffold.regenCount(node) == 0:
      weight += regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if node.isReference(): node.setValue(node.sourceNode().getValue())
      else: 
        weight += applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients)
        if node.isRequestNode(): weight += evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    scaffold.incrementRegenCount(node)

  if isinstance(node.value,SPRef) and node.value.makerNode != node and scaffold.isAAA(node.value.makerNode):
    weight += regen(trace,node.value.makerNode,scaffold,shouldRestore,omegaDB,gradients)

  return weight

