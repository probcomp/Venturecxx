import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import constructScaffold
from node import ApplicationNode, OutputNode
from lkernel import VariationalLKernel

def mixMH(trace,indexer,operator):
  index = indexer.sampleIndex(trace)
  rhoMix = indexer.logDensityOfIndex(trace,index)
  logAlpha = operator.propose(trace,index) # Mutates trace and possibly operator
  xiMix = indexer.logDensityOfIndex(trace,index)

  if math.log(random.random()) < xiMix + logAlpha - rhoMix:
    operator.accept() # May mutate trace
  else:
    operator.reject() # May mutate trace

class BlockScaffoldIndexer(object):
  def __init__(self,scope,block):
    self.scope = scope
    self.block = block

  def sampleIndex(self,trace):
    if self.scope == "default":
      if self.block == "one":
        pnode = trace.samplePrincipalNode()
        return constructScaffold(trace,[pnode])
      elif self.block == "all":
        return constructScaffold(trace,trace.rcs)
      else:
        raise Exception("INFER default scope does not admit custom blocks (%r)" % self.block)
    else:
      if self.block == "one":
        goalBlock = trace.sampleBlock(self.scope)
        pnodes = trace.scopes[self.scope][goalBlock]
      elif self.block == "all":
        blocks = trace.blocksInScope(self.scope)
        pnodeSets = [trace.scopes[self.scope][block] for block in blocks]
        pnodes = set().union(*pnodeSets)
      else:
        pnodes = trace.scopes[self.scope][self.block]
      return constructScaffold(trace,pnodes)

  def logDensityOfIndex(self,trace,scaffold):
    if self.scope == "default":
      if self.block == "one":
        return trace.logDensityOfPrincipalNode(None) # the actual principal node is irrelevant
      elif self.block == "all":
        return 0
      else:
        raise Exception("INFER default scope does not admit custom blocks (%r)" % self.block)
    else:
      if self.block == "one":
        return trace.logDensityOfBlock(self.scope,None) # The actual block in irrelevant
      elif self.block == "all":
        return 0
      else:
        return 0

class MHOperator(object):
  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold
    rhoWeight,self.rhoDB = detachAndExtract(trace,scaffold.border,scaffold)
    assertTorus(scaffold)
    xiWeight = regenAndAttach(trace,scaffold.border,scaffold,False,self.rhoDB,{})
    return xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
    assertTorus(self.scaffold)
    regenAndAttach(self.trace,self.scaffold.border,self.scaffold,True,self.rhoDB,{})

def registerVariationalLKernels(trace,scaffold):
  hasVariational = False
  for node in scaffold.regenCounts:
    if isinstance(node,ApplicationNode) and \
       not trace.isConstrainedAt(node) and \
       trace.pspAt(node).hasVariationalLKernel() and \
       not scaffold.isResampling(node.operatorNode):
      scaffold.lkernels[node] = trace.pspAt(node).getVariationalLKernel(trace,node)
      hasVariational = True
  return hasVariational

class MeanfieldOperator(object):
  def __init__(self,numIters,stepSize):
    self.numIters = numIters
    self.stepSize = stepSize
    self.delegate = None

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold
    if not registerVariationalLKernels(trace,scaffold):
      self.delegate = MHOperator()
      return self.delegate.propose(trace,scaffold)
    _,self.rhoDB = detachAndExtract(trace,scaffold.border,scaffold)
    assertTorus(scaffold)

    for i in range(self.numIters):
      gradients = {}
      gain = regenAndAttach(trace,scaffold.border,scaffold,False,OmegaDB(),gradients)
      detachAndExtract(trace,scaffold.border,scaffold)
      assertTorus(scaffold)
      for node,lkernel in scaffold.lkernels.iteritems():
        if isinstance(lkernel,VariationalLKernel):
          assert node in gradients
          lkernel.updateParameters(gradients[node],gain,self.stepSize)

    rhoWeight = regenAndAttach(trace,scaffold.border,scaffold,True,self.rhoDB,{})
    detachAndExtract(trace,scaffold.border,scaffold)
    assertTorus(scaffold)

    xiWeight = regenAndAttach(trace,scaffold.border,scaffold,False,OmegaDB(),{})
    return xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    if self.delegate is None:
      detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
      assertTorus(self.scaffold)
      regenAndAttach(self.trace,self.scaffold.border,self.scaffold,True,self.rhoDB,{})
    else:
      self.delegate.reject()
