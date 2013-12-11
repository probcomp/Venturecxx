# in class Scaffold()
# skipping some helpers
class Scaffold():

  def __init__(self,principalNodes=[],useDeltaKernels=False):
    self.drg = set() # later becomes a map { node => regenCount }
    self.absorbing = set()
    self.aaa = set()
    self.border = []

    self.disableCounts = {}
    self.brush = set()
    self.disabledRequests = set()

    self.kernels = {}

    self.findPreliminaryBorder(principalNodes)
    self.disableBrush()
    self.setRegenCounts()
    self.loadDefaultKernels(useDeltaKernels)

  def isAbsorbing(self,node): return node in self.absorbing
  def isResampling(self,node): return node in self.drg
  def isAAA(self,node): return node in self.aaa

  def addResamplingNode(self,q,node):
    if self.isAbsorbing(node): self.unregisterAbsorbing(node)
    self.drg.add(node)
    q.extend(node.children)

  def addAAANode(self,node):
    self.drg.add(node)
    self.aaa.add(node)

  def addAbsorbingNode(self,node): self.absorbing.add(node)

  def esrReferenceCanAbsorb(node):
    return isinstance(node.psp(),ESRRefOutputPSP) and \
           not self.isResampling(node.requestNode) and \
           not self.isResampling(node.esrParents[0])

  def findPreliminaryBorder(self,principalNodes):
    q = [] # (node,isPrincipal)
    for pnode in principalNodes: q.push(pnode,True)

    while q:
      node,isPrincipal = q.pop()
      if self.isResampling(node): pass
      elif isinstance(node,LookupNode): self.addResamplingNode(q,node)
      elif self.isResampling(node.operatorNode): self.addResamplingNode(q,node)
      elif node.psp().canAbsorb() and not isPrincipal: self.addAbsorbingNode(node)
      elif node.psp().childrenCanAAA(): self.addAAANode(node)
      elif esrReferenceCanAbsorb(node): self.addAbsorbingNode(node)
      else: self.addResamplingNode(q,node)

  def disableBrush(self):
    for node in self.drg: if isinstance(node,RequestNode): self.disableRequests(node)
    self.drg = { node : 0 for node in in self.drg if not node in self.brush }
    self.absorbing = set([node for node in self.absorbing if not node in self.brush])

  def disableRequests(self,node):
    if node in self.disabledRequests: return
    self.disabledRequests.add(node)
    for esrParent in node.outputNode.esrParents:
      self.disableCounts[esrParent] += 1
      if self.disableCounts[esrParent] == esrParent.numRequests:
        self.disableEval(esrParent)

  def registerBrush(self,node): self.brush.add(node)

  def registerBorder(self,node): self.border.append(node)
  def registerKernel(self,node,kernel): 
    assert not node in kernels
    self.kernels[node] = kernel

  def hasAAANodes(self): return self.aaa

  def disableEval(self,node):
    if node in self.brush: return
    self.registerBrush(node)
    if isinstance(node,OutputNode):
      self.registerBrush(node.requestNode)
      self.disableRequests(node.requestNode)
      self.disableEval(node.operatorNode)
      for operandNode in node.operandNodes: self.disableEval(operandNode)

  def setRegenCounts(self):
    for node in self.drg:
      if self.isAAA(node):
        self.drg[node].regenCount += 1
        self.registerBorder(node)
        self.registerKernel(node,node.psp().getAAAKernel())
      elif not self.hasChildInAorD(node):
        self.drg[node].regenCount = len(node.children()) + 1
        self.registerBorder(node)
      else:
        self.drg[node].regenCount = len(node.children())

    if self.hasAAANodes():
      for node in self.drg.union(absorbing): 
        for parent in node.parents(): self.maybeIncrementAAARegenCount(parent)
        for node in self.brush: 
          if isinstance(node,OutputNode): 
            for esrParent in node.esrParents: self.maybeIncrementAAARegenCount(esrParent)
          elif isinstance(node,LookupNode): self.maybeIncrementAAARegenCount(node.sourceNode)

  def maybeIncrementAAARegenCount(self,node):
    if isinstance(node.value,SPRef) and self.isAAA(node.value.makerNode): self.drg[node.value.makerNode] += 1

  def loadDefaultKernels(self,useDeltaKernels):
    for node in self.drg:
      if isinstance(node,ApplicationNode) and not self.isAAA(node) and not self.isResampling(node.operatorNode()):
        if useDeltaKernels and node.psp().hasDeltaKernel(): 
          self.registerKernel(node,node.psp().deltaKernel())
        elif node.psp().hasSimulationKernel():
          self.registerKernel(node,node.psp().simulationKernel()) # todo this should never happen

  def decrementRegenCount(self,node):
    assert node in self.drg
    self.drg[node] -= 1

  def incrementRegenCount(self,node):
    assert node in self.drg
    self.drg[node] += 1

  def regenCount(self,node):
    assert node in self.drg
    return self.drg[node]

  def hasChildInAOrD(self,node): return node.children.intersection(self.absorbing) or node.children.intersection(self.drg)
