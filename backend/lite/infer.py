import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import constructScaffold
from node import ApplicationNode, OutputNode
from lkernel import VariationalLKernel

def MHInfer(trace,pnode):
  rhoMix = trace.logDensityOfPrincipalNode(pnode)
  scaffold = constructScaffold(trace,[[pnode]])
  rhoWeight,rhoDB = detachAndExtract(trace,scaffold.border[0],scaffold)
  assertTorus(scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border[0],scaffold,False,rhoDB,{})
  xiMix = trace.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) > (xiMix + xiWeight) - (rhoMix + rhoWeight): # reject
    detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)
    regenAndAttach(trace,scaffold.border[0],scaffold,True,rhoDB,{})

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

def MeanfieldInfer(trace,pnode,numIters,stepSize):
  rhoMix = trace.logDensityOfPrincipalNode(pnode)
  scaffold = constructScaffold(trace,[[pnode]])
  if not registerVariationalLKernels(trace,scaffold): return MHInfer(trace,pnode)
  _,rhoDB = detachAndExtract(trace,scaffold.border[0],scaffold)
  assertTorus(scaffold)

  for i in range(numIters):
    gradients = {}
    gain = regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),gradients)
    detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)
    for node,lkernel in scaffold.lkernels.iteritems():
      if isinstance(lkernel,VariationalLKernel):
        assert node in gradients
        lkernel.updateParameters(gradients[node],gain,stepSize)

  rhoWeight = regenAndAttach(trace,scaffold.border[0],scaffold,True,rhoDB,{})
  detachAndExtract(trace,scaffold.border[0],scaffold)
  assertTorus(scaffold)
    
  xiWeight = regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),{})
  xiMix = trace.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) > (xiMix + xiWeight) - (rhoMix + rhoWeight): # reject
    detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)
    regenAndAttach(trace,scaffold.border[0],scaffold,True,rhoDB,{})
