import random
import numpy.random as npr
import math
import scipy.stats
from consistency import assertTorus,assertTrace
from omegadb import OmegaDB
from regen import regenAndAttach, regenAndAttachAtBorder
from detach import detachAndExtract, detachAndExtractAtBorder
from scaffold import constructScaffold
from node import ApplicationNode, Args
from lkernel import VariationalLKernel, DeterministicLKernel
from utils import sampleLogCategorical, cartesianProduct, logaddexp, FixedRandomness
from nose.tools import assert_almost_equal # Pylint misses metaprogrammed names pylint:disable=no-name-in-module
from value import VentureNumber
import copy
from exception import VentureError

class MissingEsrParentError(VentureError): pass
class NoSPRefError(VentureError): pass
# TODO Sane exception hierarchy?
# TODO Defined in a sane place, instead of "earliest place in the import graph where it is referenced"?

def mixMH(trace,indexer,operator):
  index = indexer.sampleIndex(trace)
  rhoMix = indexer.logDensityOfIndex(trace,index)
  # May mutate trace and possibly operator, proposedTrace is the mutated trace
  # Returning the trace is necessary for the non-mutating versions
  proposedTrace,logAlpha = operator.propose(trace,index)
  xiMix = indexer.logDensityOfIndex(proposedTrace,index)

  alpha = xiMix + logAlpha - rhoMix
  if math.log(random.random()) < alpha:
#    sys.stdout.write(".")
    operator.accept() # May mutate trace
  else:
#    sys.stdout.write("!")
    operator.reject() # May mutate trace

class BlockScaffoldIndexer(object):
  def __init__(self,scope,block,interval=None):
    if scope == "default" and not (block == "all" or block == "one" or block == "ordered"):
        raise Exception("INFER default scope does not admit custom blocks (%r)" % block)
    self.scope = scope
    self.block = block
    self.interval = interval

  def sampleIndex(self,trace):
    if self.block == "one": return constructScaffold(trace,[trace.getNodesInBlock(self.scope,trace.sampleBlock(self.scope))])
    elif self.block == "all": return constructScaffold(trace,[trace.getAllNodesInScope(self.scope)])
    elif self.block == "ordered": return constructScaffold(trace,trace.getOrderedSetsInScope(self.scope))
    elif self.block == "ordered_range": 
      assert self.interval
      return constructScaffold(trace,trace.getOrderedSetsInScope(self.scope,self.interval))
    else: return constructScaffold(trace,[trace.getNodesInBlock(self.scope,self.block)])

  def logDensityOfIndex(self,trace,_):
    if self.block == "one": return trace.logDensityOfBlock(self.scope)
    elif self.block == "all": return 0
    elif self.block == "ordered": return 0
    elif self.block == "ordered_range": return 0
    else: return 0

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


#### Rejection sampling

def computeRejectionBound(trace, scaffold, border):
  def logBoundAt(node):
    psp,value,args = trace.pspAt(node),trace.valueAt(node),trace.argsAt(node)
    if scaffold.hasLKernel(node):
      # TODO Is it right that the value here is the old value and the
      # new value?  Or do I need to fetch the old value from the
      # OmegaDB?
      return scaffold.getLKernel(node).weightBound(trace, value, value, args)
    else:
      # Resimulation kernel
      return psp.logDensityBound(value, args)
  # This looks an awful lot like what would happen on forcing a thunk
  # constructed by regenAndAttach for computing the logBound.
  logBound = 0
  # TODO Ignoring weight from lkernels in the DRG but off the border.
  # There should be no delta kernels when doing rejection sampling.
  # Should I assert lack of such lkernels?
  # TODO Ignoring weight from simulating latent requests, because I
  # don't know what to do about it.  Write tests that expose any
  # consequent problems?
  for node in border:
    if scaffold.isAbsorbing(node) or scaffold.isAAA(node):
      # AAA nodes are conveniently always in the border...
      logBound += logBoundAt(node)
    elif node.isObservation:
      try:
        appNode = trace.getConstrainableNode(node)
        logBound += logBoundAt(appNode)
      except MissingEsrParentError:
        raise Exception("Can't do rejection sampling when observing resimulation of unknown code")
      except NoSPRefError:
        raise Exception("Can't do rejection sampling when observing resimulation of unknown code")
  return logBound

class RejectionOperator(InPlaceOperator):
  """Rejection sampling on a scaffold.

  This is supposed to obey the semantics laid out in
  Bayesian Statistics Without Tears: A Sampling-Resampling Perspective
  A.F.M. Smith, A.E. Gelfand The American Statistician 46(2), 1992, p 84-88
  http://faculty.chicagobooth.edu/hedibert.lopes/teaching/ccis2010/1992SmithGelfand.pdf"""
  def propose(self, trace, scaffold):
    self.prepare(trace, scaffold)
    logBound = computeRejectionBound(trace, scaffold, scaffold.border[0])
    accept = False
    while not accept:
      xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
      accept = random.random() < math.exp(xiWeight - logBound)
      if not accept:
        detachAndExtract(trace, scaffold)
    return trace, 0


#### Resampling from the prior

class MHOperator(InPlaceOperator):
  def propose(self, trace, scaffold):
    rhoWeight = self.prepare(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
    return trace, xiWeight - rhoWeight


#### Variational

def registerVariationalLKernels(trace,scaffold):
  hasVariational = False
  for node in scaffold.regenCounts:
    if isinstance(node,ApplicationNode) and \
       not trace.isConstrainedAt(node) and \
       trace.pspAt(node).hasVariationalLKernel() and \
       not scaffold.isResampling(node.operatorNode):
      scaffold.lkernels[node] = trace.pspAt(node).getVariationalLKernel(Args(trace,node))
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
    _,self.rhoDB = detachAndExtract(trace,scaffold)

    for _ in range(self.numIters):
      gradients = {}
      gain = regenAndAttach(trace,scaffold,False,OmegaDB(),gradients)
      detachAndExtract(trace,scaffold)
      for node,lkernel in scaffold.lkernels.iteritems():
        if isinstance(lkernel,VariationalLKernel):
          assert node in gradients
          lkernel.updateParameters(gradients[node],gain,self.stepSize)

    rhoWeight = regenAndAttach(trace,scaffold,True,self.rhoDB,{})
    detachAndExtract(trace,scaffold)

    xiWeight = regenAndAttach(trace,scaffold,False,OmegaDB(),{})
    return trace,xiWeight - rhoWeight

  def accept(self):
    if self.delegate is None:
      pass
    else:
      self.delegate.accept()

  def reject(self):
    # TODO This is the same as MHOperator reject except for the
    # delegation thing -- abstract
    if self.delegate is None:
      detachAndExtract(self.trace,self.scaffold)
      regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})
    else:
      self.delegate.reject()


#### Enumerative Gibbs

def getCurrentValues(trace,pnodes): return [trace.valueAt(pnode) for pnode in pnodes]
def registerDeterministicLKernels(trace,scaffold,pnodes,currentValues):
  for (pnode,currentValue) in zip(pnodes,currentValues):
    assert not isinstance(currentValue,list)
    scaffold.lkernels[pnode] = DeterministicLKernel(trace.pspAt(pnode),currentValue)

def getCartesianProductOfEnumeratedValues(trace,pnodes):
  assert len(pnodes) > 0
  enumeratedValues = [trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode)) for pnode in pnodes]
  assert len(enumeratedValues) > 0
  return cartesianProduct(enumeratedValues)

class EnumerativeGibbsOperator(object):

  def propose(self,trace,scaffold):
    from particle import Particle

    assertTrace(trace,scaffold)

    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)
    allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)
    registerDeterministicLKernels(trace,scaffold,pnodes,currentValues)

    detachAndExtract(trace,scaffold)
    xiWeights = []
    xiParticles = []

    for p in range(len(allSetsOfValues)):
      newValues = allSetsOfValues[p]
      xiParticle = Particle(trace)
      assertTorus(scaffold)
      registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
      xiParticles.append(xiParticle)
      xiWeights.append(regenAndAttach(xiParticle,scaffold,False,OmegaDB(),{}))

    # Now sample a NEW particle in proportion to its weight
    finalIndex = sampleLogCategorical(xiWeights)
    self.finalParticle = xiParticles[finalIndex]
    return self.finalParticle,0

  def accept(self): self.finalParticle.commit()
  def reject(self): assert False


#### PGibbs

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
    regenAndAttachAtBorder(trace,border[i],scaffold,True,selectedDB,{})

# detach the rest of the particle
def detachRest(trace,border,scaffold,t):
  for i in reversed(range(t)):
    detachAndExtractAtBorder(trace,border[i],scaffold)


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
      (rhoWeights[t],omegaDBs[t][P]) = detachAndExtractAtBorder(trace,scaffold.border[t],scaffold)

    assertTorus(scaffold)
    xiWeights = [None for p in range(P)]

    # Simulate and calculate initial xiWeights
    for p in range(P):
      regenAndAttachAtBorder(trace,scaffold.border[0],scaffold,False,OmegaDB(),{})
      (xiWeights[p],omegaDBs[0][p]) = detachAndExtractAtBorder(trace,scaffold.border[0],scaffold)

#   for every time step,
    for t in range(1,T):
      newWeights = [None for p in range(P)]
      # Sample new particle and propagate
      for p in range(P):
        extendedWeights = xiWeights + [rhoWeights[t-1]]
        ancestorIndices[t][p] = sampleLogCategorical(extendedWeights)
        path = constructAncestorPath(ancestorIndices,t,p)
        restoreAncestorPath(trace,self.scaffold.border,self.scaffold,omegaDBs,t,path)
        regenAndAttachAtBorder(trace,self.scaffold.border[t],self.scaffold,False,OmegaDB(),{})
        (newWeights[p],omegaDBs[t][p]) = detachAndExtractAtBorder(trace,self.scaffold.border[t],self.scaffold)
        detachRest(trace,self.scaffold.border,self.scaffold,t)
      xiWeights = newWeights

    # Now sample a NEW particle in proportion to its weight
    finalIndex = sampleLogCategorical(xiWeights)

    path = constructAncestorPath(ancestorIndices,T-1,finalIndex) + [finalIndex]
    assert len(path) == T
    restoreAncestorPath(trace,self.scaffold.border,self.scaffold,omegaDBs,T,path)
    assertTrace(self.trace,self.scaffold)

    return trace,self._compute_alpha(rhoWeights[T-1], xiWeights, finalIndex)

  def _compute_alpha(self, rhoWeight, xiWeights, finalIndex):
    # Remove the weight of the chosen xi from the list instead of
    # trying to subtract in logspace to prevent catastrophic
    # cancellation (as would happen if the chosen xi weight were
    # significantly larger than all the other xi weights and the rho
    # weight).
    otherXiWeightsWithRho = copy.copy(xiWeights)
    otherXiWeightsWithRho.pop(finalIndex)
    otherXiWeightsWithRho.append(rhoWeight)

    weightMinusXi = logaddexp(otherXiWeightsWithRho)
    weightMinusRho = logaddexp(xiWeights)
    alpha = weightMinusRho - weightMinusXi
    return alpha

  def accept(self):
    pass
  def reject(self):
    detachRest(self.trace,self.scaffold.border,self.scaffold,self.T)
    assertTorus(self.scaffold)
    path = constructAncestorPath(self.ancestorIndices,self.T-1,self.P) + [self.P]
    assert len(path) == self.T
    restoreAncestorPath(self.trace,self.scaffold.border,self.scaffold,self.omegaDBs,self.T,path)
    assertTrace(self.trace,self.scaffold)


#### Functional PGibbs

class ParticlePGibbsOperator(object):
  def __init__(self,P):
    self.P = P

  def propose(self,trace,scaffold):
    from particle import Particle
    self.trace = trace
    self.scaffold = scaffold

    assertTrace(self.trace,self.scaffold)

    #print map(len, scaffold.border)

    self.T = len(self.scaffold.border)
    T = self.T
    P = self.P

#    assert T == 1 # TODO temporary
    rhoDBs = [None for t in range(T)]
    rhoWeights = [None for t in range(T)]

    for t in reversed(range(T)):
      rhoWeights[t],rhoDBs[t] = detachAndExtractAtBorder(trace,scaffold.border[t],scaffold)

    assertTorus(scaffold)

    particles = [Particle(trace) for p in range(P+1)]
    self.particles = particles

    particleWeights = [None for p in range(P+1)]


    # Simulate and calculate initial xiWeights

    for p in range(P):
      particleWeights[p] = regenAndAttachAtBorder(particles[p],scaffold.border[0],scaffold,False,OmegaDB(),{})

    particleWeights[P] = regenAndAttachAtBorder(particles[P],scaffold.border[0],scaffold,True,rhoDBs[0],{})
    assert_almost_equal(particleWeights[P],rhoWeights[0])

#   for every time step,
    for t in range(1,T):
      newParticles = [None for p in range(P+1)]
      newParticleWeights = [None for p in range(P+1)]
      # Sample new particle and propagate
      for p in range(P):
        parent = sampleLogCategorical(particleWeights)
        newParticles[p] = Particle(particles[parent])
        newParticleWeights[p] = regenAndAttachAtBorder(newParticles[p],self.scaffold.border[t],self.scaffold,False,OmegaDB(),{})
      newParticles[P] = Particle(particles[P])
      newParticleWeights[P] = regenAndAttachAtBorder(newParticles[P],self.scaffold.border[t],self.scaffold,True,rhoDBs[t],{})
      assert_almost_equal(newParticleWeights[P],rhoWeights[t])
      particles = newParticles
      particleWeights = newParticleWeights

    # Now sample a NEW particle in proportion to its weight
    finalIndex = sampleLogCategorical(particleWeights[0:-1])
    assert finalIndex < P

    self.finalIndex = finalIndex
    self.particles = particles

    return particles[finalIndex],self._compute_alpha(particleWeights, finalIndex)

  def _compute_alpha(self, particleWeights, finalIndex):
    # Remove the weight of the chosen xi from the list instead of
    # trying to subtract in logspace to prevent catastrophic
    # cancellation (for the same reason as
    # PGibbsOperator._compute_alpha)
    particleWeightsNoXi = copy.copy(particleWeights)
    particleWeightsNoXi.pop(finalIndex)

    weightMinusXi = logaddexp(particleWeightsNoXi)
    weightMinusRho = logaddexp(particleWeights[0:-1])
    alpha = weightMinusRho - weightMinusXi
    return alpha

  def accept(self):
    self.particles[self.finalIndex].commit()
    assertTrace(self.trace,self.scaffold)

  def reject(self):
    self.particles[-1].commit()
    assertTrace(self.trace,self.scaffold)

#### Slice
    
# "stepping out" procedure
# See "Slice Sampling" (Neal 2000) p11 for details
def findInterval(f,x0,logy,w,m):
  U = random.random()  
  L = x0 - w * U
  R = L + w

  V = random.random()
  J = math.floor(m * V)
  K = (m - 1) - J

  maxIters = 10000
  
  iterJ = 0
  while J > 0:
    iterJ += 1
    if iterJ == maxIters: raise Exception("Cannot find interval for slice")
    fl = f(L)
    # print "Expanding down from L", L, "f(L)", fl, "logy", logy
    if logy >= fl: break
    if math.isnan(fl): break
    L = L - w
    J = J - 1

  iterK = 0    
  while K > 0:
    iterK += 1
    if iterK == maxIters: raise Exception("Cannot find interval for slice")
    fr = f(R)
    # print "Expanding up from R", R, "f(R)", fr, "logy", logy
    if logy >= fr: break
    if math.isnan(fr): break
    R = R + w
    K = K - 1

  return L,R

def sampleInterval(f,x0,logy,L,R):
  maxIters = 10000
  it = 0
  while True:
    it += 1
    if it == maxIters: raise Exception("Cannot sample interval for slice")
    U = random.random()
    x1 = L + U * (R - L)
    fx1 = f(x1)
    # print "Slicing at x1", x1, "f(x1)", fx1, "logy", logy, "L", L, "R", R
    if logy <= fx1: return x1
    if x1 < x0: L = x1
    else: R = x1

def makeDensityFunction(trace,scaffold,psp,pnode,fixed_randomness):
  from particle import Particle
  def f(x):
    with fixed_randomness:
      scaffold.lkernels[pnode] = DeterministicLKernel(psp,VentureNumber(x))
      # The particle is a way to regen without clobbering the underlying trace
      # TODO Do repeated regens along the same scaffold actually work?
      return regenAndAttach(Particle(trace),scaffold,False,OmegaDB(),{})
  return f
  
class SliceOperator(object):

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold

    pnode = scaffold.getPNode()
    psp = trace.pspAt(pnode)
    currentVValue = trace.valueAt(pnode)
    currentValue = currentVValue.getNumber()
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,currentVValue)

    rhoWeight,self.rhoDB = detachAndExtract(trace,scaffold)

    f = makeDensityFunction(trace,scaffold,psp,pnode,FixedRandomness())
    logy = f(currentValue) + math.log(random.uniform(0,1))
    w = .5
    m = 100
    # print "Slicing with x0", currentValue, "w", w, "m", m
    L,R = findInterval(f,currentValue,logy,w,m)
    proposedValue = sampleInterval(f,currentValue,logy,L,R)
    proposedVValue = VentureNumber(proposedValue)
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,proposedVValue)
    
    xiWeight = regenAndAttach(trace,scaffold,False,self.rhoDB,{})
    return trace,xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})


#### Gradient ascent to max a-posteriori

class MAPOperator(InPlaceOperator):
  def __init__(self, epsilon, steps):
    self.epsilon = epsilon
    self.steps = steps

  def propose(self, trace, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)

    # So the initial detach will get the gradient right
    registerDeterministicLKernels(trace, scaffold, pnodes, currentValues)
    _rhoWeight = self.prepare(trace, scaffold, True) # Gradient is in self.rhoDB

    grad = GradientOfRegen(trace, scaffold, pnodes)

    # Might as well save a gradient computation, since the initial
    # detach does it
    start_grad = [self.rhoDB.getPartial(pnode) for pnode in pnodes]

    # Smashes the trace but leaves it a torus
    proposed_values = self.evolve(grad, currentValues, start_grad)

    _xiWeight = grad.regen(proposed_values) # Mutates the trace

    return (trace, 1000) # It's MAP -- try to force acceptance

  def evolve(self, grad, values, start_grad):
    xs = values
    dxs = start_grad
    for _ in range(self.steps):
      xs = [x + dx*self.epsilon for (x,dx) in zip(xs, dxs)]
      dxs = grad(xs)
    return xs

class NesterovAcceleratedGradientAscentOperator(MAPOperator):
  def step_lam(self, lam):
    return (1 + math.sqrt(1 + 4 * lam * lam))/2
  def gamma(self, lam):
    return (1 - lam) / self.step_lam(lam)
  def evolve(self, grad, values, start_grad):
    # This formula is from
    # http://blogs.princeton.edu/imabandit/2013/04/01/acceleratedgradientdescent/
    xs = values
    ys = xs
    dxs = start_grad
    lam = 1
    for _ in range(self.steps):
      gam = self.gamma(lam)
      new_ys = [x + dx*self.epsilon for (x,dx) in zip(xs, dxs)]
      new_xs = [old_y * gam + new_y * (1-gam) for (old_y, new_y) in zip(ys, new_ys)]
      (xs, ys, dxs, lam) = (new_ys, new_ys, grad(new_xs), self.step_lam(lam))
    return xs

#### Hamiltonian Monte Carlo

class GradientOfRegen(object):
  """An applicable object, calling which computes the gradient
  of regeneration along the given scaffold.  Also permits performing
  one final such regeneration without computing the gradient.  The
  value of this class is that it supports repeated regenerations (and
  gradient computations), and that it preserves the randomness across
  said regenerations (enabling gradient methods to be applied
  sensibly)."""

  # Much disastrous hackery is necessary to implement this because
  # both regen and detach mutate the scaffold (!) and regen depends
  # upon the scaffold having been detached along.  However, each new
  # regen potentially creates new brush, which has to be traversed by
  # the following corresponding detach in order to compute the
  # gradient.  So if I am going to detach and regen repeatedly, I need
  # to pass the scaffolds from one to the next and rebuild them
  # properly.
  def __init__(self, trace, scaffold, pnodes):
    self.trace = trace
    self.scaffold = scaffold
    # Pass and store the pnodes because their order matters, and the
    # scaffold has them as a set
    self.pnodes = pnodes
    self.fixed_randomness = FixedRandomness()

  def __call__(self, values):
    """Returns the gradient of the weight of regenerating along
    an (implicit) scaffold starting with the given values.  Smashes
    the trace, but leaves it a torus.  Assumes there are no delta
    kernels around."""
    # TODO Assert that no delta kernels are requested?
    self.fixed_regen(values)
    new_scaffold = constructScaffold(self.trace, [set(self.pnodes)])
    registerDeterministicLKernels(self.trace, new_scaffold, self.pnodes, values)
    (_, rhoDB) = detachAndExtract(self.trace, new_scaffold, True)
    self.scaffold = new_scaffold
    return [rhoDB.getPartial(pnode) for pnode in self.pnodes]

  def fixed_regen(self, values):
    # Ensure repeatability of randomness
    with self.fixed_randomness:
      return self.regen(values)

  def regen(self, values):
    registerDeterministicLKernels(self.trace, self.scaffold, self.pnodes, values)
    return regenAndAttach(self.trace, self.scaffold, False, OmegaDB(), {})


class HamiltonianMonteCarloOperator(InPlaceOperator):

  def __init__(self, epsilon, L):
    self.epsilon = epsilon
    self.num_steps = L

  # Notionally, I want to do Hamiltonian Monte Carlo on the potential
  # given by this function:
  #   def potential(values):
  #     registerDeterministicLKernels(trace,scaffold,pnodes,values)
  #     return -regenAndAttach(trace, scaffold, False, OmegaDB(), {})
  #
  # The trouble, of course, is that I need the gradient of this to
  # actually do HMC.
  #
  # I don't trust any of Python's extant AD libraries to get this
  # right, so I'm going to do it by implementing one level of reverse
  # mode AD myself.  Fortunately, the trace acts like a tape already.
  # Unfortunately, regen constitutes the forward phase but has no
  # reverse phase.  Fortunately, detach traverses the trace in the
  # proper order so can compute the reverse phase.  Unfortunately,
  # detach mutates the trace as it goes, so there will be some
  # machinations (perhaps I should use particles?)

  def propose(self, trace, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)

    # So the initial detach will get the gradient right
    registerDeterministicLKernels(trace, scaffold, pnodes, currentValues)
    rhoWeight = self.prepare(trace, scaffold, True) # Gradient is in self.rhoDB

    momenta = self.sampleMomenta(currentValues)
    start_K = self.kinetic(momenta)

    grad = GradientOfRegen(trace, scaffold, pnodes)
    def grad_potential(values):
      # The potential function we want is - log density
      return [-dx for dx in grad(values)]

    # Might as well save a gradient computation, since the initial
    # detach does it
    start_grad_pot = [-self.rhoDB.getPartial(pnode) for pnode in pnodes]

    # Smashes the trace but leaves it a torus
    (proposed_values, end_K) = self.evolve(grad_potential, currentValues, start_grad_pot, momenta)

    xiWeight = grad.regen(proposed_values) # Mutates the trace
    # The weight arithmetic is given by the Hamiltonian being
    # -weight + kinetic(momenta)
    return (trace, xiWeight - rhoWeight + start_K - end_K)

  def sampleMomenta(self, currentValues):
    def sample_normal(_):
      return scipy.stats.norm.rvs(loc=0, scale=1)
    return [v.map_real(sample_normal) for v in currentValues]
  def kinetic(self, momenta):
    # This is the log density of sampling these momenta, up to an
    # additive constant
    return sum([m.dot(m) for m in momenta]) / 2.0

  def evolve(self, grad_U, start_q, start_grad_q, start_p):
    epsilon = self.epsilon
    num_steps = npr.randint(int(self.num_steps))+1
    q = start_q
    # The initial momentum half-step
    dpdt = start_grad_q
    p = [pi - dpdti * (epsilon / 2.0) for (pi, dpdti) in zip(start_p, dpdt)]

    for i in range(num_steps):
      # Position step
      q = [qi + pi * epsilon for (qi, pi) in zip(q,p)]

      # Momentum step, except at the end
      if i < num_steps - 1:
        dpdt = grad_U(q)
        p = [pi - dpdti * epsilon for (pi, dpdti) in zip(p, dpdt)]

    # The final momentum half-step
    dpdt = grad_U(q)
    p = [pi - dpdti * (epsilon / 2.0) for (pi, dpdti) in zip(p, dpdt)]

    # Negate momenta at the end to make the proposal symmetric
    # (irrelevant if the kinetic energy function is symmetric)
    p = [-pi for pi in p]

    return q, self.kinetic(p)
