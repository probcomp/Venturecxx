# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import copy

from ..omegadb import OmegaDB
from ..regen import regenAndAttachAtBorder
from ..detach import detachAndExtractAtBorder
from ..utils import sampleLogCategorical
from ..utils import logaddexp
from ..consistency import assertTrace
from ..consistency import assertTorus

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
  def name(self): return "particle gibbs (mutating)"


#### Functional PGibbs

class ParticlePGibbsOperator(object):
  def __init__(self,P):
    self.P = P

  def propose(self,trace,scaffold):
    from ..particle import Particle
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
    # assert_almost_equal(particleWeights[P],rhoWeights[0])

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
      # assert_almost_equal(newParticleWeights[P],rhoWeights[t])
      particles = newParticles
      particleWeights = newParticleWeights

    finalIndex = self.select_final_particle_index(particleWeights)

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

  def select_final_particle_index(self, particleWeights):
    # Sample a new particle in proportion to its weight
    return sampleLogCategorical(particleWeights[0:-1])

  def accept(self):
    self.particles[self.finalIndex].commit()
    assertTrace(self.trace,self.scaffold)

  def reject(self):
    self.particles[-1].commit()
    assertTrace(self.trace,self.scaffold)

  def name(self): return "particle gibbs (functional)"

## CONSIDER Whether this operator actually finds the MAP or the maximum likelihood.
class ParticlePMAPOperator(ParticlePGibbsOperator):

  def select_final_particle_index(self, particleWeights):
    return particleWeights.index(max(particleWeights))

  def _compute_alpha(self, particleWeights, finalIndex):
    return 0 # This operator is not supposed to be M-H compliant

  def name(self): return "particle map (functional)"
