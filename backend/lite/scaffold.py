from node import ConstantNode, LookupNode, ApplicationNode, RequestNode, OutputNode
from psp import ESRRefOutputPSP
import pdb
from spref import SPRef

class Scaffold:
  def __init__(self,regenCounts={},absorbing=set(),aaa=set(),border=set(),lkernels={}):
    assert type(regenCounts) is dict
    self.regenCounts = regenCounts
    self.absorbing = absorbing
    self.aaa = aaa
    self.border = [x for x in border]
    self.lkernels = lkernels

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
    print "regenCounts: " + str(self.regenCounts)
    print "absorbing: " + str(self.absorbing)
    print "aaa: " + str(self.aaa)
    print "border: " + str(self.border)

def constructScaffold(trace,pnodes):
  cDRG,cAbsorbing,cAAA = findCandidateScaffold(trace,pnodes)
  brush = findBrush(trace,cDRG,cAbsorbing,cAAA)
  drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
  border = findBorder(trace,drg,absorbing,aaa)
  regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush)
  lkernels = loadKernels(trace,drg,aaa)
  return Scaffold(regenCounts,absorbing,aaa,border,lkernels)

def addResamplingNode(trace,drg,absorbing,q,node):
  if node in absorbing: absorbing.remove(node)
  drg.add(node)
  q.extend([(n,False) for n in trace.childrenAt(node)])

def esrReferenceCanAbsorb(trace,drg,node):
  return isinstance(trace.pspAt(node),ESRRefOutputPSP) and \
         not node.requestNode in drg and \
         not trace.esrParentsAt(node)[0] in drg

def findCandidateScaffold(trace,principalNodes):
  drg,absorbing,aaa = set(),set(),set()
  q = [(pnode,True) for pnode in principalNodes]

  while q:
    node,isPrincipal = q.pop()
    if node in drg: pass
    elif isinstance(node,LookupNode): addResamplingNode(trace,drg,absorbing,q,node)
    elif node.operatorNode in drg: addResamplingNode(trace,drg,absorbing,q,node)
    elif trace.pspAt(node).canAbsorb() and not isPrincipal: absorbing.add(node)
    elif esrReferenceCanAbsorb(trace,drg,node): absorbing.add(node)
    elif trace.pspAt(node).childrenCanAAA(): 
      drg.add(node)
      aaa.add(node)
    else: addResamplingNode(trace,drg,absorbing,q,node)
  return drg,absorbing,aaa

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
  if isinstance(value,SPRef) and value.makerNode != node and value.makerNode in aaa: 
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

def loadKernels(trace,drg,aaa):
  return { node : trace.pspAt(node).getAAALKernel() for node in aaa}

