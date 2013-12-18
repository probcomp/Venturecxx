import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import Scaffold

def MHInfer(trace):
  pnode = trace.samplePrincipalNode()
  rhoAux = trace.logDensityOfPrincipalNode(pnode)
  scaffold = Scaffold([pnode])
  rhoWeight,rhoDB = detachAndExtract(trace,scaffold.border,scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border,scaffold,False,rhoDB,{})
  xiAux = trace.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) > (xiAux + xiWeight) - (rhoAux + rhoWeight): # reject
    detachAndExtract(trace,scaffold.border,scaffold)
    regenAndAttach(trace,scaffold.border,scaffold,True,rhoDB,{})





# class MeanfieldGKernel(DetachAndRegenGKernel):
#   def propose(self,scaffold):
#     _,self.rhoDB = detach(self.trace,self.scaffold.border,self.scaffold)
#     self.registerVariationalKernels()
#     for i in range(numIters):
#       gradients = {}
#       gain = regenAndAttach(self.trace,self.scaffold.border,self.scaffold,False,None,gradients)
#       detachAndExtract(self.trace,self.scaffold.border,self.scaffold)
#       for node,lkernel in self.scaffold.lkernels():
#         if lkernel.isVariationalLKernel(): lkernel.updateParameters(gradients[node],gain,stepSize)

#     rhoWeight = regenAndAttach(self.trace,self.scaffold.border,self.scaffold,True,self.rhoDB,{})
#     detachAndExtract(trace,scaffold.border,scaffold)
    
#     xiWeight = regenAndAttach(trace,scaffold,border,scaffold,False,None,{})
#     return rhoWeight - xiWeight

