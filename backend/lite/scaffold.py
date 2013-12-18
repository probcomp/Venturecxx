from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from psp import ESRRefOutputPSP
import pdb
from spref import SPRef

class Scaffold():

  def __init__(self,trace,principalNodes=[],useDeltaKernels=False):
    self.trace = trace
    self.drg = set() # later becomes a map { node => regenCount }
    self.absorbing = set()
    self.aaa = set()
    self.border = []
    self.disableCounts = {}
    self.brush = set()
    self.disabledRequests = set()
    self.kernels = {}

    self.construct(principalNodes,useDeltaKernels)

  def construct(self,principalNodes,useDeltaKernels):
    # add all candidates to drg, absorbing, and aaa
    self.findPreliminaryBorder(principalNodes) 

    # remove the brush from drg, absorbing, and aaa
    # initializes all regenCounts to 0 in the drg
    self.disableBrush() 

    # computes the regenCounts for all nodes in the drg
    # adds terminal resampling nodes to the border
    # registers aaa kernels
    self.setRegenCounts() 

    # registers any additional kernels, e.g. Gaussian drift kernels
    self.loadDefaultKernels(useDeltaKernels)


  def hasKernelFor(self,node): return node in self.kernels
  def getKernel(self,node): return self.kernels[node]
  def hasChildInAorD(self,node):
    kids = self.trace.childrenAt(node)
    return kids.intersection(self.drg) or kids.intersection(self.absorbing)
  

  def isAbsorbing(self,node): return node in self.absorbing
  def isResampling(self,node): return node in self.drg
  def isAAA(self,node): return node in self.aaa

  def unregisterAbsorbing(self,node): self.absorbing.remove(node)

  def addResamplingNode(self,q,node):
    if self.isAbsorbing(node): self.unregisterAbsorbing(node)
    self.drg.add(node)
    q.extend([(n,False) for n in node.children])

  def addAAANode(self,node):
    self.drg.add(node)
    self.aaa.add(node)

  def addAbsorbingNode(self,node): 
    self.absorbing.add(node)

  def esrReferenceCanAbsorb(self,node):
    return isinstance(self.trace.pspAt(node),ESRRefOutputPSP) and \
           not self.isResampling(node.requestNode) and \
           not self.isResampling(self.trace.esrParentsAt(node)[0])

  def findPreliminaryBorder(self,principalNodes):
    q = [(pnode,True) for pnode in principalNodes]

    while q:
      node,isPrincipal = q.pop()
      if self.isResampling(node): pass
      elif isinstance(node,LookupNode): self.addResamplingNode(q,node)
      elif self.isResampling(node.operatorNode): self.addResamplingNode(q,node)
      elif self.trace.pspAt(node).canAbsorb() and not isPrincipal: self.addAbsorbingNode(node)
      elif self.trace.pspAt(node).childrenCanAAA(): self.addAAANode(node)
      elif self.esrReferenceCanAbsorb(node): self.addAbsorbingNode(node)
      else: self.addResamplingNode(q,node)

  def disableBrush(self):
    for node in self.drg:
      if isinstance(node,RequestNode): self.disableRequests(node)
    self.drg = { node : 0 for node in self.drg if not node in self.brush }
    self.absorbing = set([node for node in self.absorbing if not node in self.brush])
    self.aaa = set([node for node in self.aaa if not node in self.brush])
    self.border.extend(self.absorbing)

  def disableRequests(self,node):
    if node in self.disabledRequests: return
    self.disabledRequests.add(node)
    for esrParent in self.trace.esrParentsAt(node.outputNode):
      if not esrParent in self.disableCounts: self.disableCounts[esrParent] = 0
      self.disableCounts[esrParent] += 1
      if self.disableCounts[esrParent] == self.trace.numRequestsAt(esrParent):
        self.disableEval(esrParent)

  def registerBrush(self,node): self.brush.add(node)

  def registerBorder(self,node): self.border.append(node)
  def registerKernel(self,node,kernel): 
    assert not node in self.kernels
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
        self.drg[node] += 1
        self.registerBorder(node)
        self.registerKernel(node,self.trace.pspAt(node).getAAAKernel())
      elif not self.hasChildInAorD(node):
        self.drg[node] = len(self.trace.childrenAt(node)) + 1
        self.registerBorder(node)
      else:
        self.drg[node] = len(self.trace.childrenAt(node))

    if self.hasAAANodes():
      for node in self.absorbing.union(self.drg):
        for parent in self.trace.parentsAt(node): self.maybeIncrementAAARegenCount(parent)
      for node in self.brush: 
        if isinstance(node,OutputNode):
          for esrParent in self.trace.esrParesntsAt(node): self.maybeIncrementAAARegenCount(esrParent)
        elif isinstance(node,LookupNode): self.maybeIncrementAAARegenCount(node.sourceNode)

  def maybeIncrementAAARegenCount(self,node):
    value = self.trace.valueAt(node)
    if isinstance(value,SPRef) and self.isAAA(value.makerNode): self.drg[value.makerNode] += 1

  def loadDefaultKernels(self,useDeltaKernels):
    for node in self.drg:
      if isinstance(node,ApplicationNode) and not self.isAAA(node) and not self.isResampling(node.operatorNode):
        psp = self.trace.pspAt(node)
        if useDeltaKernels and psp.hasDeltaKernel():
          self.registerKernel(node,psp.deltaKernel())
        elif psp.hasSimulationKernel():
          self.registerKernel(node,psp.simulationKernel())

  def decrementRegenCount(self,node):
    assert node in self.drg
    self.drg[node] -= 1

  def incrementRegenCount(self,node):
    assert node in self.drg
    self.drg[node] += 1

  def regenCount(self,node):
    assert node in self.drg
    return self.drg[node]

  def show(self):
    print "---Scaffold---"
    print "drg: " + str(self.drg)
    print "absorbing: " + str(self.absorbing)
    print "border: " + str(self.border)
    print "aaa: " + str(self.aaa)


