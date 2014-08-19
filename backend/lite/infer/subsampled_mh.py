import random
import math
from matplotlib import pyplot as plt
import networkx as nx
import numpy as np
import scipy.stats as stats
from ..consistency import assertTorus
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..node import LookupNode, RequestNode, OutputNode
from ..value import SPRef
from ..scope import isScopeIncludeOutputPSP
from ..scaffold import Scaffold, constructScaffold, updateValuesAtScaffold

def constructScaffoldGlobalSection(trace,setsOfPNodes,globalBorder,useDeltaKernels = False, deltaKernelArgs = None, updateValue = False):
  cDRG,cAbsorbing,cAAA = set(),set(),set()
  indexAssignments = {}
  assert isinstance(setsOfPNodes,list)
  for i in range(len(setsOfPNodes)):
    assert isinstance(setsOfPNodes[i],set)
    extendCandidateScaffoldGlobalSection(trace,setsOfPNodes[i],globalBorder,cDRG,cAbsorbing,cAAA,indexAssignments,i)

  brush = findBrush(trace,cDRG)
  drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
  border = findBorder(trace,drg,absorbing,aaa)
  regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush)
  if globalBorder is not None:
    assert globalBorder in border
    assert globalBorder in drg
    regenCounts[globalBorder] = 1
  lkernels = loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs)
  borderSequence = assignBorderSequnce(border,indexAssignments,len(setsOfPNodes))
  scaffold = Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels,brush)
  if updateValue:
    updatedNodes = set()
    updateValuesAtScaffold(trace,scaffold,updatedNodes)

  scaffold.globalBorder = globalBorder
  scaffold.local_children = list(trace.childrenAt(globalBorder)) if globalBorder is not None else []
  scaffold.N = len(scaffold.local_children)
  return scaffold

def extendCandidateScaffoldGlobalSection(trace,pnodes,globalBorder,drg,absorbing,aaa,indexAssignments,i):
  q = [(pnode,True,None) for pnode in pnodes]

  while q:
    node,isPrincipal,parentNode = q.pop()
    if node is globalBorder and globalBorder is not None:
      drg.add(node)
      indexAssignments[node] = i
    elif node in drg and not node in aaa:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    elif isinstance(node,LookupNode) or node.operatorNode in drg:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    # TODO temporary: once we put all uncollapsed AAA procs into AEKernels, this line won't be necessary
    elif node in aaa:
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    elif (not isPrincipal) and trace.pspAt(node).canAbsorb(trace,node,parentNode):
      addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i)
    elif trace.pspAt(node).childrenCanAAA():
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    else:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)

def extendCandidateScaffold(trace,pnodes,drg,absorbing,aaa,indexAssignments,i):
  q = [(pnode,True,None) for pnode in pnodes]

  while q:
    node,isPrincipal,parentNode = q.pop()
    if node in drg and not node in aaa:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    elif isinstance(node,LookupNode) or node.operatorNode in drg:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    # TODO temporary: once we put all uncollapsed AAA procs into AEKernels, this line won't be necessary
    elif node in aaa:
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    elif (not isPrincipal) and trace.pspAt(node).canAbsorb(trace,node,parentNode):
      addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i)
    elif trace.pspAt(node).childrenCanAAA():
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    else:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)

def addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  if node in aaa: aaa.remove(node)
  drg.add(node)
  q.extend([(n,False,node) for n in trace.childrenAt(node)])
  indexAssignments[node] = i

def addAAANode(drg,aaa,absorbing,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  drg.add(node)
  aaa.add(node)
  indexAssignments[node] = i

def addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i):
  assert not node in drg
  assert not node in aaa
  absorbing.add(node)
  indexAssignments[node] = i

def findBrush(trace,cDRG):
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
  assert not drg.intersection(absorbing)
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

def loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs):
  lkernels = { node : trace.pspAt(node).getAAALKernel() for node in aaa}
  if useDeltaKernels:
    for node in drg - aaa:
      if not isinstance(node,OutputNode): continue
      if node.operatorNode in drg: continue
      for o in node.operandNodes:
        if o in drg: continue
      if trace.pspAt(node).hasDeltaKernel(): lkernels[node] = trace.pspAt(node).getDeltaKernel(deltaKernelArgs)
  return lkernels

def assignBorderSequnce(border,indexAssignments,numIndices):
  borderSequence = [[] for _ in range(numIndices)]
  for node in border:
    borderSequence[indexAssignments[node]].append(node)
  return borderSequence


def subsampledMixMH(trace,indexer,operator,Nbatch,k0,epsilon):
  # Assumptions:
  #   1. Single principal node.
  #   2. P -> single path (single lookup node or output node) -> N outgoing lookup or output nodes.
  #   3. All outgoing nodes are treated equally.
  #   4. No randomness in the local sections.
  #   5. LKernel is not used in local sections.

  # Construct the global section with a globalBorder node or None.
  global_index = indexer.sampleGlobalIndex(trace)

  global_rhoMix = indexer.logDensityOfGlobalIndex(trace,global_index)
  # Propose variables in the global section.
  # May mutate trace and possibly operator, proposedTrace is the mutated trace
  # Returning the trace is necessary for the non-mutating versions
  proposedGlobalTrace,logGlobalAlpha = operator.propose(trace,global_index)
  global_xiMix = indexer.logDensityOfGlobalIndex(trace,global_index)

  # Sample u.
  log_u = math.log(random.random())

  alpha = global_xiMix + logGlobalAlpha - global_rhoMix

  N = float(global_index.N)
  if N == 0:
    # No local sections. Regular MH.
    accept = alpha > log_u
  else:
    # Austerity MH.
    mu_0 = (log_u - alpha) / N
    perm_local_chidren = np.random.permutation(global_index.local_children)

    # Sequentially do until termination condition is met.
    mx = 0.0  # Mean of mllh.
    mx2 = 0.0 # Mean of mllh^2.
    k = 0.0   # Index of minibatch.
    n = 0.0   # Number of processed local variables.
    accept = None
    while n < N:
      # Process k'th subset of local variables subsampled w/o replacement.
      n_start = n
      n_end = min(n + Nbatch, N)
      cum_dllh = 0
      for i in xrange(int(n_start), int(n_end)):
        # Construct a local scaffold section.
        local_scaffold = indexer.sampleLocalIndex(trace,perm_local_chidren[i])
        # Compute diff of log-likelihood for i'th local variable.
        dllh = operator.evalOneLocalSection(trace, local_scaffold)
        cum_dllh += dllh
      # Compute mllh for k
      size_batch = n_end - n_start
      mllh = cum_dllh / size_batch

      # Update mx, mx2, k, n
      mx  = (size_batch * mllh        + n * mx ) / n_end
      mx2 = (size_batch * mllh * mllh + n * mx2) / n_end
      k += 1
      n = n_end

      if k < k0 and n < N:
        # Do not run testing for the first k0 minibatches.
        continue

      if n == N:
        accept = mx >= mu_0
        break
      else:
        # Compute estimated standard deviation sx.
        # For the last minibatch 1 - n / N = 0.
        sx = np.sqrt((1 - (n - 1) / (N - 1)) * (mx2 - mx * mx) / (k - 1))
        # Compute q: p-value
        q = stats.t.cdf((mx - mu_0) / sx, k - 1) # p-value
        if q <= epsilon:
          accept = False
          break
        elif q >= 1 - epsilon:
          accept = True;
          break
    assert(accept is not None)
    # print n, N, float(n) / N

  if accept:
    operator.accept() # May mutate trace
  else:
    operator.reject() # May mutate trace

class SubsampledBlockScaffoldIndexer(object):
  def __init__(self,scope,block,useDeltaKernels=False,deltaKernelArgs=None,updateValue=False):
    if scope == "default" and not (block == "all" or block == "one" or block == "ordered"):
        raise Exception("INFER default scope does not admit custom blocks (%r)" % block)
    self.scope = scope
    self.block = block
    self.useDeltaKernels = useDeltaKernels
    self.deltaKernelArgs = deltaKernelArgs
    self.updateValue = updateValue

  def sampleGlobalIndex(self,trace):
    if self.block == "one": setsOfPNodes = [trace.getNodesInBlock(self.scope,trace.sampleBlock(self.scope))]
    elif self.block == "all": setsOfPNodes = [trace.getAllNodesInScope(self.scope)]
    elif self.block == "ordered": setsOfPNodes = trace.getOrderedSetsInScope(self.scope)
    else: setsOfPNodes = [trace.getNodesInBlock(self.scope,self.block)]

    # Assumption 1. Single principal node.
    assert len(setsOfPNodes) == 1
    assert len(setsOfPNodes[0]) == 1
    pnode = next(iter(setsOfPNodes[0]))

    # Assumption 2. P -> single path (single lookup node or output node) -> N outgoing lookup or output nodes.
    node = pnode
    globalBorder = None
    while True:
      children = trace.childrenAt(node)
      if len(children) == 0:
        break
      numLONode = 0
      for child in children:
        if isinstance(child, LookupNode) or isinstance(child, OutputNode):
          numLONode += 1
          nextNode = child
          if numLONode > 1:
            break
      if numLONode > 1:
        globalBorder = node
        break
      node = nextNode
    self.globalBorder = globalBorder

    index = constructScaffoldGlobalSection(trace,setsOfPNodes,globalBorder,useDeltaKernels=self.useDeltaKernels,deltaKernelArgs=self.deltaKernelArgs,updateValue=False)

    return index

  def sampleLocalIndex(self,trace,local_child):
    assert(isinstance(local_child, LookupNode) or isinstance(local_child, OutputNode))
    setsOfPNodes = [set([local_child])]
    # Set updateValue = False because we'll do detachAndExtract manually.
    return constructScaffold(trace,setsOfPNodes,updateValue=False)

  def logDensityOfGlobalIndex(self,trace,_):
    if self.block == "one": return trace.logDensityOfBlock(self.scope)
    elif self.block == "all": return 0
    elif self.block == "ordered": return 0
    else: return 0

class SubsampledInPlaceOperator(object):
  def prepare(self, trace, global_scaffold, compute_gradient = False):
    """Record the trace and scaffold for accepting or rejecting later;
    detach along the scaffold and return the weight thereof."""
    self.trace = trace
    self.global_scaffold = global_scaffold
    rhoWeight,self.global_rhoDB = detachAndExtract(trace, global_scaffold, compute_gradient)
    assertTorus(self.global_scaffold)
    return rhoWeight

  def evalOneLocalSection(self, trace, local_scaffold, compute_gradient = False):
    globalBorder = self.global_scaffold.globalBorder
    assert(globalBorder is not None)
    ## Detach and extract
    #_,local_rhoDB = detachAndExtract(trace, local_scaffold.border[0], local_scaffold, compute_gradient)
    ## Regen and attach with the old value
    #proposed_value = trace.valueAt(self.global_scaffold.globalBorder)
    #trace.setValueAt(globalBorder, self.global_rhoDB.getValue(globalBorder))
    #regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})

    # Update with the old value.
    proposed_value = trace.valueAt(globalBorder)
    trace.setValueAt(globalBorder, self.global_rhoDB.getValue(globalBorder))
    updatedNodes = set([globalBorder])
    updateValuesAtScaffold(trace,local_scaffold,updatedNodes)

    # Detach and extract
    rhoWeight,local_rhoDB = detachAndExtract(trace, local_scaffold, compute_gradient)

    # Regen and attach with the new value
    trace.setValueAt(globalBorder, proposed_value)
    xiWeight = regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})
    return xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    # Only restore the global section.
    detachAndExtract(self.trace,self.global_scaffold)
    assertTorus(self.global_scaffold)
    regenAndAttach(self.trace,self.global_scaffold,True,self.global_rhoDB,{})

  def makeConsistent(self,trace,indexer):
    # Go through every local child and do extra and regen.
    # This is to be called at the end of a number of transitions.
    if not hasattr(self, "global_scaffold"):
      self.global_scaffold = indexer.sampleGlobalIndex(trace)
    for local_child in self.global_scaffold.local_children:
      local_scaffold = indexer.sampleLocalIndex(trace,local_child)
      _,local_rhoDB = detachAndExtract(trace, local_scaffold)
      regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})

class InPlaceOperator(object):
  def prepare(self, trace, scaffold, compute_gradient = False):
    """Record the trace and scaffold for accepting or rejecting later;
    detach along the scaffold and return the weight thereof."""
    self.trace = trace
    self.scaffold = scaffold
    rhoWeight,self.rhoDB = detachAndExtract(trace, scaffold, compute_gradient)
    assertTorus(scaffold)
    return rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    assertTorus(self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})

#### Subsampled_MH Operator
#### Resampling from the prior

class SubsampledMHOperator(SubsampledInPlaceOperator):
  def propose(self, trace, global_scaffold):
    rhoWeight = self.prepare(trace, global_scaffold)
    xiWeight = regenAndAttach(trace,global_scaffold,False,self.global_rhoDB,{})
    return trace, xiWeight - rhoWeight



