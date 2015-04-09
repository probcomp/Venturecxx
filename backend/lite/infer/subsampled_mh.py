# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import warnings
import random
import math
import numpy as np
import scipy.stats as stats
from ..exception import (SubsampledScaffoldError,
                         SubsampledScaffoldNotEffectiveWarning,
                         SubsampledScaffoldNotApplicableWarning,
                         SubsampledScaffoldStaleNodesWarning)
from ..value import SPRef
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..node import LookupNode, OutputNode
from ..scaffold import constructScaffold, updateValuesAtScaffold
from mh import BlockScaffoldIndexer, InPlaceOperator

# To apply subsampled MH, we assume the following structure in a scaffold:
# - The scaffold is partitioned into a global section and N local sections.
# - There is a single principal node and it belongs to the global section.
# - There are no brush or randomness (LKernel is not allowed) in the local
#   sections.
# - Global border a single node that separates the global and local sections.
#   - It is the first node in the downstream of the principal node that has
#     more than one Output/Lookup children.
#   - It is a resampling but not AAA node in the scaffold.
#   - It is a border node in the global section.
#   - Every child of the global border is an Output/Lookup node, and every
#     child belongs to one different local section. The children cannot
#     absorb changes from the global border. (TODO Relax the last restriction.)
#
# When a global border node is not found, i.e. empty list, the subsampled MH
# algorithm behaves the same as the regular MH.
#
# When the assumptions are not met but a global border node is incorrectly
# found, running checkApplicability will give a
# SubsampledScaffoldNotApplicableWarning.
#
# When the assumptions are all met, subsampled MH will construct the global
# section and a subset of local sections.
# - When a proposal is accepted, the remaining local sections will not be
#   constructed and their node values become stale.
# - When a proposal is rejected, the local sections that have been constructed
#   will be restored to the original values.
# - When epsilon = 0, subsampled MH will run as regular MH and no stale
#   sections will occur. But it is a little slower than regular MH by a
#   constant factor.
#
# When there exist unconstrained random choices in the border of a stale local
# section, if that node is later selected as a principal component later, it
# will not give a correct weight during inference because its parents may have
# stale values. makeConsistent is provided to update stale nodes but takes
# O(N) time.
# TODO Relax this constaint with a smart stale node tagging method.

def subsampledMixMH(trace,indexer,operator,Nbatch,k0,epsilon):
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
    perm_local_roots = []
    n = 0
  else:
    # Austerity MH.
    N = float(global_index.N)
    assert N > 1

    mu_0 = (log_u - alpha) / N
    perm_local_roots = np.random.permutation(global_index.local_roots)

    accept, n, _ = sequentialTest(mu_0, k0, Nbatch, N, epsilon,
        lambda i: operator.evalOneLocalSection(indexer, perm_local_roots[i]))

  if accept:
    operator.accept() # May mutate trace
  else:
    operator.reject(indexer, perm_local_roots, n) # May mutate trace

  # DEBUG
  # if global_index.globalBorder:
  #   operator.makeConsistent(trace,indexer)

# Sequential Testing.
def sequentialTest(mu_0, k0, Nbatch, N, epsilon, fun_dllh):
  # Sequentially do until termination condition is met.
  Nbatch = float(Nbatch)
  N = float(N)
  mx = 0.0  # Mean of llh.
  mx2 = 0.0 # Mean of llh^2.
  k = 0.0   # Index of minibatch.
  n = 0.0   # Number of processed local variables.
  cum_dllh = 0.0
  cum_dllh2 = 0.0
  tstat = None
  accept = None
  while n < N:
    # Process k'th subset of local variables subsampled w/o replacement.
    n_start = n
    n_end = min(n + Nbatch, N)
    for i in xrange(int(n_start), int(n_end)):
      dllh = fun_dllh(i)
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
        tstat = (mx - mu_0) / sx
        q = stats.t.cdf(tstat, n - 1) # p-value
      # If epsilon = 0, keep drawing until n reaches N even if sx = 0.
      if q < epsilon:
        accept = False
        break
      elif q > 1 - epsilon:
        accept = True
        break
  assert accept is not None
  tstat = tstat if tstat else np.inf if accept else -np.inf
  return accept, n, tstat

class SubsampledBlockScaffoldIndexer(BlockScaffoldIndexer):
  def sampleGlobalIndex(self,trace):
    setsOfPNodes = self.getSetsOfPNodes(trace)

    # If it's empty, the subsampled scaffold is the same as a regular scaffold.
    globalBorder = self.findGlobalBorder(trace, setsOfPNodes)
    self.globalBorder = globalBorder

    # Construct the bounded scaffold.
    index = constructScaffold(trace,setsOfPNodes,useDeltaKernels=self.useDeltaKernels,deltaKernelArgs=self.deltaKernelArgs,hardBorder=globalBorder,updateValues=self.updateValues)
    index.globalBorder = globalBorder

    if globalBorder:
      # Quick check for the validity of the global border after a global section
      # is constructed.
      # More thorough and slower check can be done by calling checkApplicability.
      if not all(any(node in border for border in index.border) and
                 index.isResampling(node) and
                 not index.isAAA(node) for node in globalBorder):
        raise SubsampledScaffoldError("Invalid global border.")
      index.local_roots = list(trace.childrenAt(globalBorder[0]))
      index.N = len(index.local_roots)

    return index

  def sampleLocalIndex(self,trace,local_root,globalBorder):
    if not (isinstance(local_root, LookupNode) or
        (isinstance(local_root, OutputNode) and
         len(globalBorder) == 1 and
         not trace.pspAt(local_root).canAbsorb(trace, local_root, globalBorder[0]))):
      raise SubsampledScaffoldError("Invalid local root node.")
    setsOfPNodes = [set([local_root])]
    # Set updateValues = False because we'll update values in evalOneLocalSection.
    index = constructScaffold(trace,setsOfPNodes,updateValues=False)

    # Local section should not have brush.
    if index.brush:
      raise SubsampledScaffoldError("Local section should not have brush.")
    return index

  # Raise three types of warnings:
  # - SubsampledScaffoldNotEffectiveWarning: calling subsampled_mh will be the
  #   same as calling mh.
  # - SubsampledScaffoldNotApplicableWarning: calling subsampled_mh will cause
  #   incorrect behavior.
  # - SubsampledScaffoldStaleNodesWarning: stale node will affect the
  #   inference of other random variables. This is not a critical
  #   problem but requires one to call makeConsistent before other
  #   random nodes are selected as principal nodes.
  #
  # This method cannot check all potential problems caused by stale nodes.
  def checkApplicability(self, trace):
    block_list = [self.block] if self.block != "one" else trace.blocksInScope(self.scope)
    block_old = self.block
    for block in block_list:
      self.block = block
      setsOfPNodes = self.getSetsOfPNodes(trace)

      # If the global border empty, the subsampled scaffold is the same
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
      if not self.checkOneSection(trace, index,
          lambda: self.traverseTrace(trace, allNodes, set(globalBorder), False, set()),
          lambda: self.sampleGlobalIndex(trace), False):
        return False

      # Find the local sections from the scaffold.
      assert len(globalBorder) == 1 # This should already be guaranteed in findGlobalBorder.
      local_roots = trace.childrenAt(globalBorder[0])
      for local_root in local_roots:
        if not self.checkOneSection(trace, index,
            lambda: self.traverseTrace(trace, allNodes, {local_root}, True, set(globalBorder)),
            lambda: self.sampleLocalIndex(trace, local_root, globalBorder), True):
          return False

    self.block = block_old
    return True

  def checkOneSection(self, trace, index, traverser, sectionIndexer, isLocal):
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

    # Check if local section border include unconstrained random choices.
    # It may cause a problem when stale sections occure (e.g. when epsilon > 0).
    if isLocal:
      border_list = [n for border in sectionIndex.border for n in border]
      for border in border_list:
        if trace.pspAt(border).isRandom() and border not in trace.ccs:
          warnings.warn("Unconstrained random choices in local sections.",
                        SubsampledScaffoldStaleNodesWarning)
          break

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
  # Compute diff of log-likelihood for a local section with the root node local_root.
  def evalOneLocalSection(self, indexer, local_root, compute_gradient = False):
    trace = self.trace
    globalBorder = self.scaffold.globalBorder
    assert len(globalBorder) == 1

    # Construct a local scaffold section.
    local_scaffold = indexer.sampleLocalIndex(trace, local_root, globalBorder)

    # Get the single node.
    globalBorderNode = globalBorder[0]

    # A safer but slower way to update values. It's now replaced by the next
    # updating lines but may be useful for debugging purposes.
    #
    ## Detach and extract
    # _,local_rhoDB = detachAndExtract(trace, local_scaffold.border[0], local_scaffold, compute_gradient)
    ## Regen and attach with the old value
    # proposed_value = trace.valueAt(globalBorderNode)
    # trace.setValueAt(globalBorderNode, self.rhoDB.getValue(globalBorderNode))
    # regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})

    # Update with the old value.
    proposed_value = trace.valueAt(globalBorderNode)
    trace.setValueAt(globalBorderNode, self.rhoDB.getValue(globalBorderNode))
    updateValuesAtScaffold(trace,local_scaffold,set(globalBorder))

    # Detach and extract
    rhoWeight,local_rhoDB = detachAndExtract(trace, local_scaffold, compute_gradient)

    # Regen and attach with the new value
    trace.setValueAt(globalBorderNode, proposed_value)
    xiWeight = regenAndAttach(trace,local_scaffold,False,local_rhoDB,{})
    return xiWeight - rhoWeight

  def reject(self, indexer, perm_local_roots, n):
    # Restore the global section.
    super(SubsampledInPlaceOperator, self).reject()

    # Restore local sections in perm_local_roots[0:n]
    globalBorder = self.scaffold.globalBorder
    if globalBorder:
      for i in range(int(n)):
        local_root = perm_local_roots[i]
        local_scaffold = indexer.sampleLocalIndex(self.trace, local_root, globalBorder)
        updateValuesAtScaffold(self.trace,local_scaffold,set(globalBorder))

  # Go through every local child and do extract and regen.
  # This is to be called at the end of a number of transitions.
  def makeConsistent(self,trace,indexer):
    if hasattr(self, "scaffold"):
      self.makeConsistentGivenGlobal(trace,indexer,self.scaffold)
    else:
      # If a global section does not exist yet, try every possible block value.
      block_list = ([indexer.block] if indexer.block != "one"
                    else trace.blocksInScope(indexer.scope))
      block_old = indexer.block
      for block in block_list:
        indexer.block = block
        scaffold = indexer.sampleGlobalIndex(trace)
        self.makeConsistentGivenGlobal(trace,indexer,scaffold)
      indexer.block = block_old

  # Make consistent local sections given a global scaffold.
  def makeConsistentGivenGlobal(self,trace,indexer,scaffold):
    # Go through every local child and do extract and regen.
    # This is to be called at the end of a number of transitions.
    if scaffold.globalBorder:
      for local_root in scaffold.local_roots:
        local_scaffold = indexer.sampleLocalIndex(trace,local_root,
            scaffold.globalBorder)
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

