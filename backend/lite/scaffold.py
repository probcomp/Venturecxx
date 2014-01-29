from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from psp import ESRRefOutputPSP
from spref import SPRef

class Scaffold:
  def __init__(self,setsOfPNodes=None,regenCounts=None,absorbing=None,aaa=None,border=None,lkernels=None):
    self.setsOfPNodes = setsOfPNodes if setsOfPNodes else []
    self.regenCounts = regenCounts if regenCounts else {}
    self.absorbing = absorbing if absorbing else set()
    self.aaa = aaa if aaa else set()
    self.border = border if border else []
    self.lkernels = lkernels if lkernels else {}

  def getPrincipalNodes(self): return set.union(*self.setsOfPNodes)
  def getRegenCount(self,node): return self.regenCounts[node]
  def incrementRegenCount(self,node): self.regenCounts[node] += 1
  def decrementRegenCount(self,node): self.regenCounts[node] -= 1
  def isResampling(self,node): return node in self.regenCounts
  def isAbsorbing(self,node): return node in self.absorbing
  def isAAA(self,node): return node in self.aaa
  def hasLKernel(self,node): return node in self.lkernels
  def getLKernel(self,node): return self.lkernels[node]

  def show(self):
    print "---Scaffold---"
    print "regenCounts: " + str(len(self.regenCounts))
    print "absorbing: " + str(len(self.absorbing))
    print "aaa: " + str(len(self.aaa))
    print "border: " + str(len(self.border))

def constructScaffold(trace,setsOfPNodes,useDeltaKernels = True):
  cDRG,cAbsorbing,cAAA = set(),set(),set()
  indexAssignments = {}
  assert isinstance(setsOfPNodes,list)
  for i in range(len(setsOfPNodes)):
    assert isinstance(setsOfPNodes[i],set)
    extendCandidateScaffold(trace,setsOfPNodes[i],cDRG,cAbsorbing,cAAA,indexAssignments,i)

  brush = findBrush(trace,cDRG,cAbsorbing,cAAA)
  drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
  border = findBorder(trace,drg,absorbing,aaa)
  regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush)
  lkernels = loadKernels(trace,drg,aaa,useDeltaKernels)
  borderSequence = assignBorderSequnce(border,indexAssignments,len(setsOfPNodes))
  return Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels)

def addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  if node in aaa: aaa.remove(node)
  drg.add(node)
  q.extend([(n,False) for n in trace.childrenAt(node)])
  indexAssignments[node] = i

def addAbsorbingNode(absorbing,node,indexAssignments,i):
  absorbing.add(node)
  indexAssignments[node] = i

def addAAANode(drg,aaa,node,indexAssignments,i):
  drg.add(node)
  aaa.add(node)
  indexAssignments[node] = i

def esrReferenceCanAbsorb(trace,drg,node):
  return isinstance(trace.pspAt(node),ESRRefOutputPSP) and \
         not node.requestNode in drg and \
         not trace.esrParentsAt(node)[0] in drg

def extendCandidateScaffold(trace,pnodes,drg,absorbing,aaa,indexAssignments,i):
  q = [(pnode,True) for pnode in pnodes]

  while q:
    node,isPrincipal = q.pop()
    if node in drg and not node in aaa: pass
    elif isinstance(node,LookupNode) or node.operatorNode in drg:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    elif (trace.pspAt(node).canAbsorb() or esrReferenceCanAbsorb(trace,drg,node)) and not isPrincipal: 
      addAbsorbingNode(absorbing,node,indexAssignments,i)
    elif trace.pspAt(node).childrenCanAAA(): 
      addAAANode(drg,aaa,node,indexAssignments,i)
    else: 
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)


def findBrush(trace,cDRG,cAbsorbing,cAAA):
  disableCounts = {}
  disabledRequests = set()
  brush = set()
  for node in cDRG:
    if isinstance(node,RequestNode):
      disableRequests(trace,node,disableCounts,disabledRequests,brush)
  return brush

def disableRequests(trace,node,disableCounts,disabledRequests,brush):
  if node in disabledRequests: return
  disabledRequests.add(node)
  for esrParent in trace.esrParentsAt(node.outputNode):
    if not esrParent in disableCounts: disableCounts[esrParent] = 0
    disableCounts[esrParent] += 1
    if disableCounts[esrParent] == esrParent.numRequests:
      disableFamily(trace,esrParent,disableCounts,disabledRequests,brush)

def disableFamily(trace,node,disableCounts,disabledRequests,brush):
  if node in brush: return
  brush.add(node)
  if isinstance(node,OutputNode):
    brush.add(node.requestNode)
    disableRequests(trace,node.requestNode,disableCounts,disabledRequests,brush)
    disableFamily(trace,node.operatorNode,disableCounts,disabledRequests,brush)
    for operandNode in node.operandNodes: 
      disableFamily(trace,operandNode,disableCounts,disabledRequests,brush)

def removeBrush(cDRG,cAbsorbing,cAAA,brush):
  drg = cDRG - brush
  absorbing = cAbsorbing - brush
  aaa = cAAA - brush
  assert aaa.issubset(drg)
  return drg,absorbing,aaa

def hasChildInAorD(trace,drg,absorbing,node):
  kids = trace.childrenAt(node)
  return kids.intersection(drg) or kids.intersection(absorbing)

def findBorder(trace,drg,absorbing,aaa):
  border = absorbing.union(aaa)
  for node in drg - aaa:
    if not hasChildInAorD(trace,drg,absorbing,node): border.add(node)
  return border

def maybeIncrementAAARegenCount(trace,regenCounts,aaa,node):
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode in aaa: 
    regenCounts[value.makerNode] += 1

def computeRegenCounts(trace,drg,absorbing,aaa,border,brush):
  regenCounts = {}
  for node in drg:
    if node in aaa:
      regenCounts[node] = 1 # will be added to shortly
    elif node in border:
      regenCounts[node] = len(trace.childrenAt(node)) + 1
    else:
      regenCounts[node] = len(trace.childrenAt(node))
  
  if aaa:
    for node in drg.union(absorbing):
      for parent in trace.parentsAt(node):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,parent)

    for node in brush:
      if isinstance(node,OutputNode):
        for esrParent in trace.esrParentsAt(node):
          maybeIncrementAAARegenCount(trace,regenCounts,aaa,esrParent)
      elif isinstance(node,LookupNode):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,node.sourceNode)

  return regenCounts

def loadKernels(trace,drg,aaa,useDeltaKernels):
  lkernels = { node : trace.pspAt(node).getAAALKernel() for node in aaa}
  if useDeltaKernels:
    for node in drg - aaa:
      if not isinstance(node,OutputNode): continue
      if node.operatorNode in drg: continue
      for o in node.operandNodes:
        if o in drg: continue
      if trace.pspAt(node).hasDeltaKernel(): lkernels[node] = trace.pspAt(node).getDeltaKernel()
  return lkernels

def assignBorderSequnce(border,indexAssignments,numIndices):
  borderSequence = [[] for i in range(numIndices)]
  for node in border:
    borderSequence[indexAssignments[node]].append(node)
  return borderSequence
