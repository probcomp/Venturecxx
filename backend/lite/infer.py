import random
import math
from consistency import assertTorus,assertTrace,assertSameScaffolds
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import constructScaffold
from node import ApplicationNode, OutputNode
from lkernel import VariationalLKernel, DeterministicLKernel
from utils import simulateCategorical, cartesianProduct
from nose.tools import assert_almost_equal
import sys
import copy

def mixMH(trace,indexer,operator):
  index = indexer.sampleIndex(trace)
  pnodes = index.getPrincipalNodes().copy()
  rhoMix = indexer.logDensityOfIndex(trace,index)
  # May mutate trace and possibly operator, proposedTrace is the mutated trace
  # This is necessary for the non-mutating versions
  proposedTrace,logAlpha = operator.propose(trace,index) 
  xiMix = indexer.logDensityOfIndex(proposedTrace,index)

  alpha = xiMix + logAlpha - rhoMix
  if math.log(random.random()) < alpha:
#    sys.stdout.write("<accept>")
#    print "<accept(%d)>"%alpha
    operator.accept() # May mutate trace
  else:
#    sys.stdout.write("<reject>")
#    print "<reject(%d)>"%alpha
    operator.reject() # May mutate trace

class BlockScaffoldIndexer(object):
  def __init__(self,scope,block):
    if scope == "default" and not (block == "all" or block == "one" or block == "ordered"):
        raise Exception("INFER default scope does not admit custom blocks (%r)" % block)
    self.scope = scope
    self.block = block

  def sampleIndex(self,trace):
    if self.block == "one": return constructScaffold(trace,[trace.sampleBlock(self.scope)])
    elif self.block == "all": return constructScaffold(trace,[trace.getAllNodesInScope(self.scope)])
    elif self.block == "ordered": return constructScaffold(trace,trace.getOrderedSetsInScope(self.scope))
    else: return constructScaffold(trace,[trace.getNodesInBlock(self.scope,self.block)])

  def logDensityOfIndex(self,trace,scaffold):
    if self.block == "one": return trace.logDensityOfBlock(self.scope)
    elif self.block == "all": return 0
    elif self.block == "ordered": return 0
    else: return 0

class MHOperator(object):
  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold
    self.setsOfPNodes = [self.scaffold.getPrincipalNodes().copy()]
    rhoWeight,self.rhoDB = detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)
    xiWeight = regenAndAttach(trace,scaffold.border[0],scaffold,False,self.rhoDB,{})
    return trace,xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    # start debug
    newScaffold = constructScaffold(self.trace,self.setsOfPNodes)
    assertSameScaffolds(self.scaffold,newScaffold)
    # end debug
    detachAndExtract(self.trace,self.scaffold.border[0],self.scaffold)
    assertTorus(self.scaffold)
    regenAndAttach(self.trace,self.scaffold.border[0],self.scaffold,True,self.rhoDB,{})


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
    _,self.rhoDB = detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)

    for i in range(self.numIters):
      gradients = {}
      gain = regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),gradients)
      detachAndExtract(trace,scaffold.border[0],scaffold)
      assertTorus(scaffold)
      for node,lkernel in scaffold.lkernels.iteritems():
        if isinstance(lkernel,VariationalLKernel):
          assert node in gradients
          lkernel.updateParameters(gradients[node],gain,self.stepSize)

    rhoWeight = regenAndAttach(trace,scaffold.border[0],scaffold,True,self.rhoDB,{})
    detachAndExtract(trace,scaffold.border[0],scaffold)
    assertTorus(scaffold)

    xiWeight = regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),{})
    return trace,xiWeight - rhoWeight

  def accept(self): 
    if self.delegate is None:
      pass
    else:
      self.delegate.accept()

  def reject(self):
    if self.delegate is None:
      detachAndExtract(self.trace,self.scaffold.border[0],self.scaffold)
      assertTorus(self.scaffold)
      regenAndAttach(self.trace,self.scaffold.border[0],self.scaffold,True,self.rhoDB,{})
    else:
      self.delegate.reject()


################## Enumerative Gibbs

def getCurrentValues(trace,pnodes): return [trace.valueAt(pnode) for pnode in pnodes]
def registerDeterministicLKernels(trace,scaffold,pnodes,currentValues):
  for (pnode,currentValue) in zip(pnodes,currentValues):
    assert not isinstance(currentValue,list)
    scaffold.lkernels[pnode] = DeterministicLKernel(trace.pspAt(pnode),currentValue)

def getCartesianProductOfEnumeratedValues(trace,pnodes):
  assert len(pnodes) > 0
  enumeratedValues = [[v for v in trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode))] for pnode in pnodes]
  assert len(enumeratedValues) > 0
  cp = cartesianProduct(enumeratedValues)
  # This line is confusing! But it seems to work.
  if not type(cp[0]) is list: cp = [[x] for x in cp]
  return cp

class EnumerativeGibbsOperator(object):

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold
    assertTrace(self.trace,self.scaffold)

    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)
    allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)
    registerDeterministicLKernels(trace,scaffold,pnodes,currentValues)

    rhoWeight,self.rhoDB = detachAndExtract(trace,scaffold.border[0],scaffold)
    assert isinstance(self.rhoDB,OmegaDB)
    assertTorus(scaffold)
    xiWeights = []
    xiDBs = []

    for newValues in allSetsOfValues:
      if newValues == currentValues: continue
      assertTorus(scaffold)
      registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
      xiWeights.append(regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),{}))
      xiDBs.append(detachAndExtract(trace,scaffold.border[0],scaffold)[1])

    # Now sample a NEW particle in proportion to its weight
    finalIndex = simulateCategorical([math.exp(w) for w in xiWeights])
    xiWeight = xiWeights[finalIndex]
    self.xiDB = xiDBs[finalIndex]

    weightMinusXi = math.log(sum([math.exp(w) for w in xiWeights]) + math.exp(rhoWeight) - math.exp(xiWeight))
    weightMinusRho = math.log(sum([math.exp(w) for w in xiWeights]))

    regenAndAttach(self.trace,self.scaffold.border[0],self.scaffold,True,self.xiDB,{})

    return trace,weightMinusRho - weightMinusXi

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold.border[0],self.scaffold)
    assertTorus(self.scaffold)
    regenAndAttach(self.trace,self.scaffold.border[0],self.scaffold,True,self.rhoDB,{})




      
################## PGibbs

# Construct ancestor path backwards
def constructAncestorPath(ancestorIndices,t,n):
  if t > 0: path = [ancestorIndices[t][n]]
  else: path = []

  for i in reversed(range(1,t)): path.insert(0, ancestorIndices[i][path[0]])
  assert len(path) == t
  return path

# Restore the particle along the ancestor path
def restoreAncestorPath(trace,border,scaffold,omegaDBs,t,path):
  for i in range(t):
    selectedDB = omegaDBs[i][path[i]]
    regenAndAttach(trace,border[i],scaffold,True,selectedDB,{})

# detach the rest of the particle
def detachRest(trace,border,scaffold,t):
  for i in reversed(range(t)): 
    detachAndExtract(trace,border[i],scaffold)


# P particles, not including RHO
# T groups of sinks, with T-1 resampling steps
# and then one final resampling step to select XI
class PGibbsOperator(object):
  def __init__(self,P):
    self.P = P

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold

    assertTrace(self.trace,self.scaffold)
  
    self.T = len(self.scaffold.border)
    T = self.T
    P = self.P

    rhoWeights = [None for t in range(T)]
    omegaDBs = [[None for p in range(P+1)] for t in range(T)]
    ancestorIndices = [[None for p in range(P)] + [P] for t in range(T)]

    self.omegaDBs = omegaDBs
    self.ancestorIndices = ancestorIndices

    for t in reversed(range(T)):
      (rhoWeights[t],omegaDBs[t][P]) = detachAndExtract(trace,scaffold.border[t],scaffold)

    assertTorus(scaffold)
    xiWeights = [None for p in range(P)]

    # Simulate and calculate initial xiWeights
    for p in range(P):
      regenAndAttach(trace,scaffold.border[0],scaffold,False,OmegaDB(),{})
      (xiWeights[p],omegaDBs[0][p]) = detachAndExtract(trace,scaffold.border[0],scaffold)

#   for every time step,
    for t in range(1,T):
      newWeights = [None for p in range(P)]
      # Sample new particle and propagate
      for p in range(P):
        extendedWeights = xiWeights + [rhoWeights[t-1]]
        ancestorIndices[t][p] = simulateCategorical([math.exp(w) for w in extendedWeights])
        path = constructAncestorPath(ancestorIndices,t,p)
        restoreAncestorPath(trace,self.scaffold.border,self.scaffold,omegaDBs,t,path)
        regenAndAttach(trace,self.scaffold.border[t],self.scaffold,False,OmegaDB(),{})
        (newWeights[p],omegaDBs[t][p]) = detachAndExtract(trace,self.scaffold.border[t],self.scaffold)
        detachRest(trace,self.scaffold.border,self.scaffold,t)
      xiWeights = newWeights

    # Now sample a NEW particle in proportion to its weight
    finalIndex = simulateCategorical([math.exp(w) for w in xiWeights])
    rhoWeight = rhoWeights[T-1]
    xiWeight = xiWeights[finalIndex]

    weightMinusXi = math.log(sum([math.exp(w) for w in xiWeights]) + math.exp(rhoWeight) - math.exp(xiWeight))
    weightMinusRho = math.log(sum([math.exp(w) for w in xiWeights]))

    path = constructAncestorPath(ancestorIndices,T-1,finalIndex) + [finalIndex]
    assert len(path) == T
    restoreAncestorPath(trace,self.scaffold.border,self.scaffold,omegaDBs,T,path)
    assertTrace(self.trace,self.scaffold)

    alpha = weightMinusRho - weightMinusXi
    return trace,alpha

  def accept(self):
    pass
  def reject(self):
    detachRest(self.trace,self.scaffold.border,self.scaffold,self.T)
    assertTorus(self.scaffold)
    path = constructAncestorPath(self.ancestorIndices,self.T-1,self.P) + [self.P]
    assert len(path) == self.T
    restoreAncestorPath(self.trace,self.scaffold.border,self.scaffold,self.omegaDBs,self.T,path)
    assertTrace(self.trace,self.scaffold)


### Non-mutating PGibbs

class ParticlePGibbsOperator(object):
  def __init__(self,P):
    self.P = P

  def propose(self,trace,scaffold):
    from particle import Particle
    self.trace = trace
    self.scaffold = scaffold

    assertTrace(self.trace,self.scaffold)
  
    self.T = len(self.scaffold.border)
    T = self.T
    P = self.P

    assert T == 1 # TODO temporary
    rhoDBs = [None for t in range(T)]    
    rhoWeights = [None for t in range(T)]

    for t in reversed(range(T)):
      rhoWeights[t],rhoDBs[t] = detachAndExtract(trace,scaffold.border[t],scaffold)

      
    assertTorus(scaffold)

    particles = [Particle(trace=trace) for p in range(P+1)]
    self.particles = particles
    
    particleWeights = [None for p in range(P+1)]

    
    # Simulate and calculate initial xiWeights

    for p in range(P):
      particleWeights[p] = regenAndAttach(particles[p],scaffold.border[0],scaffold,False,OmegaDB(),{})

    particleWeights[P] = regenAndAttach(particles[P],scaffold.border[0],scaffold,True,rhoDBs[0],{})
    assert_almost_equal(particleWeights[P],rhoWeights[0])
          
#   for every time step,
    for t in range(1,T):
      newParticles = [None for p in range(P+1)]
      newParticleWeights = [None for p in range(P+1)]
      # Sample new particle and propagate
      for p in range(P):
        parent = simulateCategorical([math.exp(w) for w in particleWeights])
        newParticles[p] = Particle(particle=particles[parent])
        newParticleWeights[p] = regenAndAttach(newParticles[p],self.scaffold.border[t],self.scaffold,False,OmegaDB(),{})
      newParticles[P] = Particle(particle=particles[P])
      newParticleWeights[P] = regenAndAttach(newParticles[P],self.scaffold.border[t],self.scaffold,True,rhoDBs[t],{})
      assert_almost_equal(particleWeights[P],rhoWeights[t])
      particles = newParticles
      particleWeights = newParticleWeights

    # Now sample a NEW particle in proportion to its weight
    finalIndex = simulateCategorical([math.exp(w) for w in particleWeights[0:-1]])
    assert finalIndex < P
    xiWeight = particleWeights[finalIndex]
    rhoWeight = particleWeights[-1]

    totalExpWeight = sum([math.exp(w) for w in particleWeights])
    totalXiExpWeight = sum([math.exp(w) for w in particleWeights[0:-1]])
    weightMinusXi = math.log(totalExpWeight - math.exp(xiWeight))
    weightMinusRho = math.log(totalXiExpWeight)

#    print particleWeights,weightMinusXi,weightMinusRho
    alpha = weightMinusRho - weightMinusXi

    self.finalIndex = finalIndex

    # TODO need to return a trace as well
    return particles[finalIndex],alpha

  def accept(self):
    self.particles[self.finalIndex].commit()
    assertTrace(self.trace,self.scaffold)    
    
  def reject(self):
    self.particles[-1].commit()
    assertTrace(self.trace,self.scaffold)
    
