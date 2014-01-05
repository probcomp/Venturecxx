def __init__(self,principalNodeSets):
  self.drgSets = [{} for i in principalNodeSets]
  self.absorbingSets = [set() for i in principalNodeSets]
  self.aaa = set()
  self.disableCounts = {}

  for i in range(len(principalNodeSets)):
    self.addToPreliminaryScaffold(principalNodeSets[i],i)
    
  self.disableBrush()
  self.setRegenCounts()
  self.loadDefaultKernels(useDeltaKernels)

def addResamplingNode(self,q,node,i):
  if self.isAbsorbing(node): self.unregisterAbsorbing(node)
  if self.isResampling(node): return
  self.drgSets[i][node] = {"regenCount" : 0 }
  q.extend(node.children())

def addAAANode(self,node,i):
  self.drgSets[i][node] = {"regenCount" : 0 }
  self.aaa.add(node)

def addAbsorbingNode(self,node,i): 
  if not self.isAbsorbing(node): self.absorbingSets[i].add(node)
  
def addToPreliminaryScaffold(self,principalNodes,i):
  q = [] # (node,isPrincipal)
  for pnode in principalNodes: q.push(pnode,True)

  while q:
    node,isPrincipal = q.pop()
    if self.isResampling(node): pass
    elif node.isLookupNode(): self.addResamplingNode(q,node,i)
    elif self.isResampling(node.operatorNode()): self.addResamplingNode(q,node,i)
    elif node.psp().canAbsorb() and not isPrincipal: self.addAbsorbingNode(node,i)
    elif node.psp().childrenCanAAA(): self.addAAANode(node,i)
    elif esrReferenceCanAbsorb(node): self.addAbsorbingNode(node,i)
    else: self.addResamplingNode(q,node,i)
