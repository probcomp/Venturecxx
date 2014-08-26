import random
import math
import numpy as np
import scipy.stats as stats
from ..consistency import assertTorus
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..node import LookupNode, RequestNode, OutputNode
from ..value import SPRef
from ..scaffold import constructScaffold, constructScaffoldGlobalSection, updateValuesAtScaffold
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

  N = float(global_index.N)
  if N == 0:
    # No local sections. Regular MH.
    accept = alpha > log_u
  else:
    # Austerity MH.
    mu_0 = (log_u - alpha) / N
    perm_local_chidren = np.random.permutation(global_index.local_children)

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
        local_scaffold = indexer.sampleLocalIndex(trace,perm_local_chidren[i])
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
        q = stats.t.cdf((mx - mu_0) / sx, n - 1) # p-value
        if q <= epsilon:
          accept = False
          break
        elif q >= 1 - epsilon:
          accept = True
          break
    assert accept is not None

  if accept:
    operator.accept() # May mutate trace
  else:
    operator.reject() # May mutate trace

class SubsampledBlockScaffoldIndexer(BlockScaffoldIndexer):
  def sampleGlobalIndex(self,trace):
    setsOfPNodes = self.getSetsOfPNodes(trace)

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
    assert isinstance(local_child, LookupNode) or isinstance(local_child, OutputNode)
    setsOfPNodes = [set([local_child])]
    # Set updateValue = False because we'll update values in evalOneLocalSection.
    return constructScaffold(trace,setsOfPNodes,updateValue=False)

  def name(self):
    return ["subsampled_scaffold", self.scope, self.block] + ([self.interval] if self.interval is not None else []) + ([self.true_block] if hasattr(self, "true_block") else [])

# When accepting/rejecting a proposal, only accept/restore the global section.
# The local sections are left in the state when returned from subsampledMixMH.
class SubsampledInPlaceOperator(InPlaceOperator):
  def evalOneLocalSection(self, trace, local_scaffold, compute_gradient = False):
    globalBorder = self.scaffold.globalBorder
    assert globalBorder is not None

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
    updatedNodes = set([globalBorder])
    updateValuesAtScaffold(trace,local_scaffold,updatedNodes)

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

