import warnings
import random
import math
import numpy as np
import scipy.stats as stats
from ..exception import (SubsampledScaffoldError,
                         SubsampledScaffoldNotEffectiveWarning,
                         SubsampledScaffoldNotApplicableWarning)
from ..value import SPRef
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..node import LookupNode, OutputNode
from ..scaffold import constructScaffold, updateValuesAtScaffold
from mh import BlockScaffoldIndexer, InPlaceOperator

def subsampledMixMH(trace,indexer,operator,Nbatch,k0,epsilon):
  # Assumptions:
  #   1. Single principal node.
  #   2. P -> single path (single lookup node or output node) -> N outgoing lookup or output nodes.
  #   3. All outgoing nodes are treated equally.
  #   4. No randomness in the local sections.
  #   5. LKernel is not used in local sections.

  # Construct the global section with a globalBorder node or None.
  global_index = indexer.sampleGlobalIndex(trace)

  global_rhoMix = indexer.logDensityOfIndex(trace,global_index)
  # Propose variables in the global section.
  # May mutate trace and possibly operator, proposedTrace is the mutated trace
  # Returning the trace is necessary for the non-mutating versions
  proposedGlobalTrace,logGlobalAlpha = operator.propose(trace,global_index)
  global_xiMix = indexer.logDensityOfIndex(proposedGlobalTrace,global_index)

  # Sample u.
  log_u = math.log(random.random())

  alpha = global_xiMix + logGlobalAlpha - global_rhoMix

  if not global_index.globalBorder:
    # No local sections. Regular MH.
    accept = alpha > log_u
  else:
    # Austerity MH.
    N = float(global_index.N)
    assert N > 1

    mu_0 = (log_u - alpha) / N
    perm_local_roots = np.random.permutation(global_index.local_roots)

    # Sequentially do until termination condition is met.
    mx = 0.0  # Mean of llh.
    mx2 = 0.0 # Mean of llh^2.
    k = 0.0   # Index of minibatch.
    n = 0.0   # Number of processed local variables.
    cum_dllh = 0.0
    cum_dllh2 = 0.0
    accept = None
    while n < N:
      # Process k'th subset of local variables subsampled w/o replacement.
      n_start = n
      n_end = min(n + Nbatch, N)
      for i in xrange(int(n_start), int(n_end)):
        # Construct a local scaffold section.
        local_scaffold = indexer.sampleLocalIndex(
            trace,perm_local_roots[i],global_index.globalBorder)
        # Compute diff of log-likelihood for i'th local variable.
        dllh = operator.evalOneLocalSection(trace, local_scaffold)
        cum_dllh  += dllh
        cum_dllh2 += dllh * dllh

      # Update k, n, mx, mx2
      k += 1
      n = n_end
      mx  = cum_dllh  / n_end
      mx2 = cum_dllh2 / n_end

      if k < k0 and n < N:
        # Do not run testing for the first k0 minibatches.
        continue

      if n == N:
        accept = mx >= mu_0
        break
      else:
        # Compute estimated standard deviation sx.
        # For the last minibatch 1 - n / N = 0.
        sx = np.sqrt((1 - (n - 1) / (N - 1)) * (mx2 - mx * mx) / (n - 1))
        # Compute q: p-value
        if sx == 0:
          q = 1 if mx >= mu_0 else 0
        else:
          q = stats.t.cdf((mx - mu_0) / sx, n - 1) # p-value
        # If epsilon = 0, keep drawing until n reaches N even if sx = 0.
        if q < epsilon:
          accept = False
          break
        elif q > 1 - epsilon:
          accept = True
          break
    assert accept is not None

  if accept:
    operator.accept() # May mutate trace
  else:
    operator.reject() # May mutate trace

  # DEBUG
  # if global_index.globalBorder:
  #   operator.makeConsistent(trace,indexer)

class SubsampledBlockScaffoldIndexer(BlockScaffoldIndexer):
  def sampleGlobalIndex(self,trace):
    setsOfPNodes = self.getSetsOfPNodes(trace)

    # If it's empty, the subsampled scaffold is the same
    # as a regular scaffold.
    globalBorder = self.findGlobalBorder(trace, setsOfPNodes)
    self.globalBorder = globalBorder

    # Construct the bounded scaffold.
    index = constructScaffold(trace,setsOfPNodes,useDeltaKernels=self.useDeltaKernels,deltaKernelArgs=self.deltaKernelArgs,hardBorder=globalBorder,updateValues=self.updateValues)

    # Check if it's a valid partition.
    index.globalBorder = globalBorder
    if globalBorder:
      if not all(node in index.border and index.isResampling(node) and
                 not index.isAAA(node) for node in globalBorder):
        raise SubsampledScaffoldError("Invalid global border.")
      index.local_roots = list(trace.childrenAt(globalBorder[0]))
      index.N = len(index.local_roots)

    # TODO Check if local sections have intersection with each other.

    return index

  def sampleLocalIndex(self,trace,localRoot,globalBorder):
    # TODO Remove the restriction that a local root cannot be an absorbing node.
    if not (isinstance(localRoot, LookupNode) or
        (isinstance(localRoot, OutputNode) and
         len(globalBorder) == 1 and
         not trace.pspAt(localRoot).canAbsorb(trace, localRoot, globalBorder[0]))):
      raise SubsampledScaffoldError("Invalid local root node.")
    setsOfPNodes = [set([localRoot])]
    # Set updateValues = False because we'll update values in evalOneLocalSection.
    index = constructScaffold(trace,setsOfPNodes,updateValues=False)

    # Local section should not have brush.
    if index.brush:
      raise SubsampledScaffoldError("Local section should not have brush.")
    return index

  # Raise two types of warnings:
  # - SubsampledScaffoldNotEffectiveWarning: calling subsampled_mh will be the
  #   same as calling mh.
  # - SubsampledScaffoldNotApplicableWarning: calling subsampled_mh will cause
  #   a incorrect behavior.
  def checkApplicability(self, trace):
    # Check cannot be done with a random set of PNodes.
    # assert self.block != "one" or len(trace.blocksInScope(self.scope)) == 1
    if self.block == "one" and len(trace.blocksInScope(self.scope)) > 1:
      warnings.warn("Check cannot be done with a random set of PNodes.")
      return False
    setsOfPNodes = self.getSetsOfPNodes(trace)

    # If it's empty, the subsampled scaffold is the same
    # as a regular scaffold.
    globalBorder = self.findGlobalBorder(trace, setsOfPNodes)
    if not globalBorder:
      warnings.warn("No global border found. subsampled_mh will behave the "
                    "same as mh.", SubsampledScaffoldNotEffectiveWarning)
      return False

    # Construct the regular scaffold.
    index = self.sampleIndex(trace)
    if not all(index.isResampling(node) and not index.isAAA(node)
               for node in globalBorder):
      warnings.warn("Invalid global border.", SubsampledScaffoldNotApplicableWarning)
      return False
    allNodes = self.allNodesInScaffold(index)

    # Check the global section.
    if not self.checkOneSection(index,
        lambda: self.traverseTrace(trace, allNodes, set(globalBorder), False, set()),
        lambda: self.sampleGlobalIndex(trace)):
      return False

    # Find the local sections from the scaffold.
    assert len(globalBorder) == 1 # This should already be guaranteed in findGlobalBorder.
    localRootNodes = trace.childrenAt(globalBorder[0])
    for localRoot in localRootNodes:
      if not self.checkOneSection(index,
          lambda: self.traverseTrace(trace, allNodes, {localRoot}, True, set(globalBorder)),
          lambda: self.sampleLocalIndex(trace, localRoot, globalBorder)):
        return False

    return True

  def checkOneSection(self, index, traverser, sectionIndexer):
    # Find the node set of a section from the scaffold by graph traversal.
    success, nodeSet = traverser()
    if not success:
      warnings.warn("The global border does not seperate sections.",
                    SubsampledScaffoldNotApplicableWarning)
      return False

    # Construct a scaffold section using the indexer.
    try:
      sectionIndex = sectionIndexer()
    except SubsampledScaffoldError as e:
      warnings.warn(e.message, SubsampledScaffoldNotApplicableWarning)
      return False

    # Compare the two sets of nodes.
    if not (nodeSet == self.allNodesInScaffold(sectionIndex) and
            all(self.checkType(n, index, sectionIndex) for n in nodeSet)):
      warnings.warn("The scaffold section is not consistent with the entire scaffold.",
                    SubsampledScaffoldNotApplicableWarning)
      return False

    return True

  def checkType(self, node, index1, index2):
    return (index1.isResampling(node) == index2.isResampling(node) and
            index1.isAbsorbing(node)  == index2.isAbsorbing(node) and
            index1.isAAA(node)        == index2.isAAA(node) and
            (node in index1.brush)    == (node in index2.brush))

  def allNodesInScaffold(self, index):
    return set(index.regenCounts.keys()) | index.absorbing | index.brush

  def traverseTrace(self, trace, include, startSet, descend, failAt):
    nodeSet = set()
    q = list(startSet & include)
    while q:
      node = q.pop()
      if node not in nodeSet:
        nodeSet.add(node)

        toExtend = set()
        if node not in startSet or descend:
          toExtend = toExtend.union(trace.childrenAt(node))
        if node not in startSet or not descend:
          toExtend = toExtend.union(trace.parentsAt(node))
        for n in toExtend:
          if n in failAt: return False, set()
          if n in include: q.append(n)
    return True, nodeSet

  def findGlobalBorder(self, trace, setsOfPNodes):
    # Find the globalBorder. Return an empty list if the desired structure
    # does not exist. However, the validity of the returned value is not
    # guaranteed.

    # Assumption 1. Single principal node.
    # assert len(setsOfPNodes) == 1
    # assert len(setsOfPNodes[0]) == 1
    if not (len(setsOfPNodes) == 1 and len(setsOfPNodes[0]) == 1):
      return []
    pnode = next(iter(setsOfPNodes[0]))

    # Assumption 2. P -> single path (single lookup node or output node) -> N outgoing lookup or output nodes.
    node = pnode
    globalBorder = []
    while True:
      maybeBorder = True
      children = trace.childrenAt(node)
      if len(children) == 0:
        break
      numLONode = 0
      for child in children:
        if isinstance(child, (LookupNode, OutputNode)):
          numLONode += 1
          nextNode = child
        else:
          # The global border can not have children other than lookup or output node.
          maybeBorder = False
      if numLONode > 1:
        globalBorder.append(node)
        break
      node = nextNode
    assert len(globalBorder) <= 1
    if globalBorder:
      # assert maybeBorder
      # assert not isinstance(trace.valueAt(globalBorder[0]), SPRef)
      # assert not trace.pspAt(globalBorder[0]).childrenCanAAA()
      if not (maybeBorder and 
          not isinstance(trace.valueAt(globalBorder[0]), SPRef) and
          not trace.pspAt(globalBorder[0]).childrenCanAAA()):
        # Is not a valid globalBorder. Revert to regular MH.
        globalBorder = []
    return globalBorder

  def name(self):
    return ["subsampled_scaffold", self.scope, self.block] + ([self.interval] if self.interval is not None else []) + ([self.true_block] if hasattr(self, "true_block") else [])

# When accepting/rejecting a proposal, only accept/restore the global section.
# The local sections are left in the state when returned from subsampledMixMH.
class SubsampledInPlaceOperator(InPlaceOperator):
  def evalOneLocalSection(self, trace, local_scaffold, compute_gradient = False):
    assert len(self.scaffold.globalBorder) == 1
    # Take the single node.
    globalBorder = self.scaffold.globalBorder[0]

    # A safer but slower way to update values. It's now replaced by the next
    # updating lines but may be useful for debugging purposes.
    #
    ## Detach and extract
    # _,local_rhoDB = detachAndExtract(trace, local_scaffold.border[0], local_scaffold, compute_gradient)
    ## Regen and attach with the old value
    # proposed_value = trace.valueAt(self.scaffold.globalBorder)
    # trace.setValueAt(globalBorder, self.rhoDB.getValue(globalBorder))
    # regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})

    # Update with the old value.
    proposed_value = trace.valueAt(globalBorder)
    trace.setValueAt(globalBorder, self.rhoDB.getValue(globalBorder))
    updateValuesAtScaffold(trace,local_scaffold,set([globalBorder]))

    # Detach and extract
    rhoWeight,local_rhoDB = detachAndExtract(trace, local_scaffold, compute_gradient)

    # Regen and attach with the new value
    trace.setValueAt(globalBorder, proposed_value)
    xiWeight = regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})
    return xiWeight - rhoWeight

  def makeConsistent(self,trace,indexer):
    # Go through every local child and do extra and regen.
    # This is to be called at the end of a number of transitions.
    if not hasattr(self, "scaffold"):
      self.scaffold = indexer.sampleGlobalIndex(trace)
    if self.scaffold.globalBorder:
      for local_root in self.scaffold.local_roots:
        local_scaffold = indexer.sampleLocalIndex(trace,local_root)
        _,local_rhoDB = detachAndExtract(trace, local_scaffold)
        regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})

#### Subsampled_MH Operator
#### Resampling from the prior

class SubsampledMHOperator(SubsampledInPlaceOperator):
  def propose(self, trace, scaffold):
    rhoWeight = self.prepare(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
    return trace, xiWeight - rhoWeight

  def name(self): return "resimulation subsampled MH"

