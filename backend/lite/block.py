def findPrincipalNodesInSubblock(trace,block,subblock):
  pnodes = set()
  for root in trace.getRootsForSubblock(block,subblock):
    addUpstreamRandomChoices(trace,root,block,subblock,pnodes)
  return pnodes

def addUpstreamRandomChoices(trace,node,block,subblock,pnodes):
  if not node.isOutputNode(): return
  if node.psp().isRandom(): pnodes.add(node)
  if node.requestNode().psp().isRandom(): pnodes.add(node.requestNode())
  for (id,exp,env,otherBlock,otherSubblock) in esrs:
    if not (block == otherBlock and subblock != otherSubblock):
      addUpstreamRandomChoices(trace,node.spaux().getFamily(id),block,subblock,pnodes)

  addUpstreamRandomChoices(trace,node.operatorNode(),block,subblock,pnodes)
  for operandNode in node.operandNodes():
    addUpstreamRandomChoices(trace,node.operandNode(),block,subblock,pnodes)

    
