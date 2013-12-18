from abc import ABCMeta, abstractmethod
import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import Scaffold

class GKernel(object):
  __metaclass__ = ABCMeta
  def __init__(self,trace): self.trace = trace

  def infer(self,N):
    if not self.trace.rcs: raise Exception("No random choices to do inference on ")
    assert len(self.trace.rcs) > 0
    for n in range(N):
      alpha = self.propose()
      logU = math.log(random.random())
#      print "alpha: " + str(alpha)
      if logU < alpha: self.accept()
      else: self.reject()

  @abstractmethod
  def propose(self): pass

  def accept(self): pass
  def reject(self): pass

  def loadParameters(self,params): pass

class MixMHGKernel(GKernel):
  __metaclass__ = ABCMeta

  def __init__(self,trace,childGKernel):
    super(MixMHGKernel,self).__init__(trace)
    self.childGKernel = childGKernel

  @abstractmethod
  def sampleIndex(self): pass

  @abstractmethod
  def logDensityOfIndex(self,index): pass

  @abstractmethod
  def processIndex(self,index): pass

  def propose(self):
    index = self.sampleIndex()
    weightRho = self.logDensityOfIndex(index)
    self.childGKernel.loadParameters(self.processIndex(index))
    alpha = self.childGKernel.propose()
    weightXi = self.logDensityOfIndex(index);
    return alpha + weightXi - weightRho

  def accept(self): self.childGKernel.accept()
  def reject(self): self.childGKernel.reject()

class OutermostMixMHGKernel(MixMHGKernel):
  def sampleIndex(self): return self.trace.samplePrincipalNode()
  def logDensityOfIndex(self,index): return self.trace.logDensityOfPrincipalNode(index)
  def processIndex(self,index): return (Scaffold(self.trace,[index]),index)

class DetachAndRegenGKernel(GKernel):
  def loadParameters(self,params): self.scaffold = params[0]

  def propose(self):
    rhoWeight,self.rhoDB = detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
    assertTorus(self.scaffold)
    xiWeight = regenAndAttach(self.trace,self.scaffold.border,self.scaffold,False,self.rhoDB,{})
    return xiWeight - rhoWeight

  def accept(self): 
    pass

  def reject(self): 
    detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
    assertTorus(self.scaffold)
    regenAndAttach(self.trace,self.scaffold.border,self.scaffold,True,self.rhoDB,{})

class MeanfieldGKernel(DetachAndRegenGKernel):
  def propose(self,scaffold):
    _,self.rhoDB = detach(self.trace,self.scaffold.border,self.scaffold)
    self.registerVariationalKernels()
    for i in range(numIters):
      gradients = {}
      gain = regenAndAttach(self.trace,self.scaffold.border,self.scaffold,False,None,gradients)
      detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
      for node,lkernel in self.scaffold.lkernels():
        if lkernel.isVariationalLKernel(): lkernel.updateParameters(gradients[node],gain,stepSize)

    rhoWeight = regenAndAttach(self.trace,self.scaffold.border,self.scaffold,True,self.rhoDB,{})
    detachAndExtract(trace,scaffold.border,scaffold)
    
    xiWeight = regenAndAttach(trace,scaffold,border,scaffold,False,None,{})
    return rhoWeight - xiWeight

