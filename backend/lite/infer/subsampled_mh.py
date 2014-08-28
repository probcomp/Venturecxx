import random
import math
import numpy as np
import scipy.stats as stats
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
    perm_local_children = np.random.permutation(global_index.local_children)

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
        local_scaffold = indexer.sampleLocalIndex(trace,perm_local_children[i])
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

    # Find the globalBorder. If it's empty, the subsampled scaffold is the same
    # as a regular scaffold.

    # Assumption 1. Single principal node.
    assert len(setsOfPNodes) == 1
    assert len(setsOfPNodes[0]) == 1
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
    self.globalBorder = globalBorder
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

    # Construct the bounded scaffold.
    index = constructScaffold(trace,setsOfPNodes,useDeltaKernels=self.useDeltaKernels,deltaKernelArgs=self.deltaKernelArgs,hardBorder=globalBorder,updateValues=self.updateValues)

    # Check if it's a valid partition.
    index.globalBorder = globalBorder
    if globalBorder:
      assert (index.isResampling(globalBorder[0]) and
              not index.isAAA(globalBorder[0]))
      index.local_children = list(trace.childrenAt(globalBorder[0]))
      index.N = len(index.local_children)

    # TODO Check if local sections have intersection with each other.

    return index

  def sampleLocalIndex(self,trace,local_child):
    assert isinstance(local_child, (LookupNode, OutputNode))
    setsOfPNodes = [set([local_child])]
    # Set updateValues = False because we'll update values in evalOneLocalSection.
    index = constructScaffold(trace,setsOfPNodes,updateValues=False)

    # Local section should not have brush.
    assert not index.brush
    return index

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
      for local_child in self.scaffold.local_children:
        local_scaffold = indexer.sampleLocalIndex(trace,local_child)
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

