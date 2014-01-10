import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import Scaffold
from node import ApplicationNode, OutputNode
from lkernel import VariationalLKernel

def mixMH(trace,scope,block,operator):
  if not(scope == "default"):
    raise Exception("INFER custom scopes not yet implemented (%r)" % params)
  if not(block == "one"):
    raise Exception("INFER custom blocks not yet implemented (%r)" % params)

  pnode = trace.samplePrincipalNode()
  rhoMix = trace.logDensityOfPrincipalNode(pnode)
  scaffold = Scaffold(trace,[pnode])
  logAlpha = operator.propose(trace,scaffold) # Mutates trace and possibly operator
  xiMix = trace.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) < xiMix + logAlpha - rhoMix:
    operator.accept() # May mutate trace
  else:
    operator.reject() # May mutate trace

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
  for node in scaffold.drg:
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
