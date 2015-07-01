# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

import random
import math
import time
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..scaffold import constructScaffold
from ..lkernel import DeterministicLKernel

def getCurrentValues(trace,pnodes): return [trace.valueAt(pnode) for pnode in pnodes]

def registerDeterministicLKernels(trace,scaffold,pnodes,currentValues):
  for (pnode,currentValue) in zip(pnodes,currentValues):
    assert not isinstance(currentValue,list)
    scaffold.lkernels[pnode] = DeterministicLKernel(trace.pspAt(pnode),currentValue)

def unregisterDeterministicLKernels(_trace,scaffold,pnodes):
  for pnode in pnodes:
    del scaffold.lkernels[pnode]

def getCurrentValuesWithAddresses(trace,pnodes): return [(pnode.address, trace.valueAt(pnode)) for pnode in pnodes]

def registerDeterministicLKernelsByAddress(trace,scaffold,addressesAndValues):
  nodes = dict([(node.address, node) for node in scaffold.getPrincipalNodes()])
  for (addr,currentValue) in addressesAndValues:
    assert not isinstance(currentValue,list)
    assert addr in nodes
    node = nodes[addr]
    scaffold.lkernels[node] = DeterministicLKernel(trace.pspAt(node),currentValue)

def mixMH(trace,indexer,operator):
  start = time.time()
  index = indexer.sampleIndex(trace)

  # record node addresses and values for the benefit of the profiler
  if trace.profiling_enabled:
    nodes = index.getPrincipalNodes()
    current = [trace.valueAt(node) for node in nodes]
    getAddr = lambda node: node.address
    principal = map(getAddr, nodes)
    absorbing = map(getAddr, index.absorbing)
    aaa = map(getAddr, index.aaa)
    brush = len(index.brush)

  rhoMix = indexer.logDensityOfIndex(trace,index)
  # May mutate trace and possibly operator, proposedTrace is the mutated trace
  # Returning the trace is necessary for the non-mutating versions
  proposedTrace,logAlpha = operator.propose(trace,index)
  xiMix = indexer.logDensityOfIndex(proposedTrace,index)

  # record the proposed values for the profiler
  if trace.profiling_enabled:
    proposed = [trace.valueAt(node) for node in nodes]

  alpha = xiMix + logAlpha - rhoMix
  if math.log(random.random()) < alpha:
#    sys.stdout.write(".")
    operator.accept() # May mutate trace
    accepted = True
  else:
#    sys.stdout.write("!")
    operator.reject() # May mutate trace
    accepted = False

  if trace.profiling_enabled:
    trace.recordProposal(
      operator = operator.name(),
      indexer = indexer.name(),
      time = time.time() - start,
      logscore = trace.getGlobalLogScore(),
      current = current,
      proposed = proposed,
      accepted = accepted,
      alpha = alpha,
      principal = principal,
      absorbing = absorbing,
      aaa = aaa,
      brush = brush
    )

class BlockScaffoldIndexer(object):
  def __init__(self,scope,block,interval=None,useDeltaKernels=False,deltaKernelArgs=None,updateValues=False):
    if scope == "default" and not (block == "all" or block == "none" or block == "one" or block == "ordered"):
        raise Exception("INFER default scope does not admit custom blocks (%r)" % block)
    self.scope = scope
    self.block = block
    self.interval = interval
    self.useDeltaKernels = useDeltaKernels
    self.deltaKernelArgs = deltaKernelArgs
    self.updateValues = updateValues

  def getSetsOfPNodes(self,trace):
    if self.block == "one":
      self.true_block = trace.sampleBlock(self.scope)
      setsOfPNodes = [trace.getNodesInBlock(self.scope,self.true_block)]
    elif self.block == "all": setsOfPNodes = [trace.getAllNodesInScope(self.scope)]
    elif self.block == "none": setsOfPNodes = [set()]
    elif self.block == "ordered": setsOfPNodes = trace.getOrderedSetsInScope(self.scope)
    elif self.block == "ordered_range":
      assert self.interval
      setsOfPNodes = trace.getOrderedSetsInScope(self.scope,self.interval)
    else: setsOfPNodes = [trace.getNodesInBlock(self.scope,self.block)]
    return setsOfPNodes

  def sampleIndex(self,trace):
    setsOfPNodes = self.getSetsOfPNodes(trace)
    return constructScaffold(trace,setsOfPNodes,useDeltaKernels=self.useDeltaKernels,deltaKernelArgs=self.deltaKernelArgs,updateValues=self.updateValues)

  def logDensityOfIndex(self,trace,_):
    if self.block == "one": return trace.logDensityOfBlock(self.scope)
    elif self.block == "all": return 0
    elif self.block == "none": return 0
    elif self.block == "ordered": return 0
    elif self.block == "ordered_range": return 0
    else: return 0

  def name(self):
    return ["scaffold", self.scope, self.block] + ([self.interval] if self.interval is not None else []) + ([self.true_block] if hasattr(self, "true_block") else [])

class InPlaceOperator(object):
  def prepare(self, trace, scaffold, compute_gradient = False):
    """Record the trace and scaffold for accepting or rejecting later;
    detach along the scaffold and return the weight thereof."""
    self.trace = trace
    self.scaffold = scaffold
    rhoWeight,self.rhoDB = detachAndExtract(trace, scaffold, compute_gradient)
    return rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})

#### Resampling from the prior

class MHOperator(InPlaceOperator):
  def propose(self, trace, scaffold):
    rhoWeight = self.prepare(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
    return trace, xiWeight - rhoWeight

  def name(self): return "resimulation MH"




