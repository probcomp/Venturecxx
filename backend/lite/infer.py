class GKernel():
  def __init__(self,trace): self.trace = trace
  def propose(self): @abstract
  def accept(self): @abstract
  def reject(self): @abstract
  def loadParameters(self): @abstract

class MixMHGKernel(GKernel):
  def __init__(self,trace,childGKernel):
    super(self,GKernel).__init__(trace)
    self.childGKernel = childGKernel

  def sampleIndex(self): @abstract
  def logDensityOfIndex(self,index): @abstract
  def processIndex(self,index): @abstract

  def propose(self):
    index = self.sampleIndex()
    weightRho = self.logDensityOfIndex(index)
    alpha = childGKernel.propose(self.processIndex(index))
    weightXi = self.logDensityOfIndex(index);
    return alpha + weightXi - weightRho

  def accept(self): childGKernel.accept()
  def reject(self): childGKernel.reject()

class OutermostMixMHGKernel(MixMHGKernel):
  def sampleIndex(self): return trace.sampleRandomChoiceUniformly()
  def logDensityOfIndex(self,index): return -log(trace.numRandomChoices())
  def processIndex(self,index): return (Scaffold(index),index)


class detachAndRegenGKernel():
  def propose(self,scaffold):
    rhoWeight,self.rhoDB = detach(self.trace,self.scaffold.border(),self.scaffold)
    xiWeight = regen(self.trace,self.scaffold.border(),self.scaffold,False,self.rhoDB)
    return xiWeight - rhoWeight

  def accept(self): pass
  def reject(self): 
    detach(trace,scaffold.border(),scaffold)
    regen(trace,scaffold.border(),scaffold,True,rhoDB)

class meanfieldGKernel(DetachAndRegenGKernel):
  def propose(self,scaffold):
    _,rhoDB = detach(self.trace,self.scaffold.border(),self.scaffold)
    self.registerVariationalKernels()
    for i in range(numIters):
      gradients = {}
      gain = regen(self.trace,self.scaffold.border(),self.scaffold,False,None,gradients)
      detach(self.trace,self.scaffold.border(),self.scaffold)
      for node,lkernel in scaffold.lkernels():
        if lkernel.isVariationalLKernel(): lkernel.updateParameters(gradients[node],gain,stepSize)

    rhoWeight = regen(trace,scaffold.border(),scaffold,True,rhoDB)
    detach(trace,scaffold.border(),scaffold)
    
    xiWeight = regen(trace,scaffold,border(),scaffold,False,None)
    return rhoWeight - xiWeight

class enumerationGKernel(
