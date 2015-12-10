# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..utils import sampleLogCategorical, cartesianProduct
from ..consistency import assertTrace, assertTorus
from venture.lite.infer.mh import getCurrentValues
from venture.lite.infer.mh import registerDeterministicLKernels
from venture.lite.infer.mh import registerDeterministicLKernelsByAddress

def getCartesianProductOfEnumeratedValues(trace,pnodes):
  enumeratedValues = [trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode)) for pnode in pnodes]
  return cartesianProduct(enumeratedValues)

def getCartesianProductOfEnumeratedValuesWithAddresses(trace,pnodes):
  enumeratedValues = [[(pnode.address, v) for v in trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode))] for pnode in pnodes]
  return cartesianProduct(enumeratedValues)

class EnumerativeGibbsOperator(object):

  def compute_particles(self,trace,scaffold):
    assertTrace(trace,scaffold)

    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)
    allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)

    registerDeterministicLKernels(trace,scaffold,pnodes,currentValues)

    rhoWeight, rhoDB = detachAndExtract(trace,scaffold)
    xiWeights = []
    xiParticles = []

    for p in range(len(allSetsOfValues)):
      newValues = allSetsOfValues[p]
      if newValues == currentValues:
        # If there are random choices downstream, keep their current values.
        # This follows the auxiliary variable method in Neal 2000,
        # "Markov Chain Sampling Methods for Dirichlet Process Models"
        # (Algorithm 8 with m = 1).
        # Otherwise, we may target the wrong stationary distribution.
        # See test/inference_language/test_enumerative_gibbs.py for an example.
        shouldRestore = True
        omegaDB = rhoDB
      else:
        shouldRestore = False
        omegaDB = OmegaDB()
      xiParticle = self.copy_trace(trace)
      assertTorus(scaffold)
      registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
      xiParticles.append(xiParticle)
      xiWeights.append(regenAndAttach(xiParticle,scaffold,shouldRestore,omegaDB,{}))
      # if shouldRestore:
      #   assert_almost_equal(xiWeights[-1], rhoWeight)
    return (xiParticles, xiWeights)

  def propose(self, trace, scaffold):
    (xiParticles, xiWeights) = self.compute_particles(trace, scaffold)
    # Now sample a NEW particle in proportion to its weight
    finalIndex = self.chooseProposalParticle(xiWeights)
    self.finalParticle = xiParticles[finalIndex]
    return self.finalParticle,0

  def copy_trace(self, trace):
    from ..particle import Particle
    return Particle(trace)

  def chooseProposalParticle(self, xiWeights):
    return sampleLogCategorical(xiWeights)

  def accept(self): self.finalParticle.commit()
  def reject(self): assert False
  def name(self): return "enumerative gibbs"

class EnumerativeMAPOperator(EnumerativeGibbsOperator):
  def chooseProposalParticle(self, xiWeights):
    m = max(xiWeights)
    return [i for i, j in enumerate(xiWeights) if j == m][0]
  def name(self): return "enumerative max a-posteriori"

class EnumerativeDiversify(EnumerativeGibbsOperator):
  def __init__(self, copy_trace):
    super(EnumerativeDiversify, self).__init__()
    self.copy_trace = copy_trace

  def __call__(self, trace, scaffolder):
    # CONSDIER how to unify this code with EnumerativeGibbsOperator.
    # Problems:
    # - a torus cannot be copied by copy_trace
    # - a particle cannot be copied by copy_trace either
    # - copy_trace undoes incorporation (on Lite traces)

    scaffold = scaffolder.sampleIndex(trace)
    assertTrace(trace,scaffold)

    pnodes = scaffold.getPrincipalNodes()
    allSetsOfValues = getCartesianProductOfEnumeratedValuesWithAddresses(trace,pnodes)

    xiWeights = []
    xiParticles = []

    for newValuesWithAddresses in allSetsOfValues:
      xiParticle = self.copy_trace(trace)
      xiParticle.makeConsistent() # CONSIDER what to do with the weight from this
      # Impossible original state is probably fine
      # ASSUME the scaffolder is deterministic. Have to make the
      # scaffold again b/c detach mutates it, and b/c it may not work
      # across copies of the trace.
      scaffold = scaffolder.sampleIndex(xiParticle)
      (rhoWeight, _) = detachAndExtract(xiParticle, scaffold)
      assertTorus(scaffold)
      registerDeterministicLKernelsByAddress(xiParticle,scaffold,newValuesWithAddresses)
      xiWeight = regenAndAttach(xiParticle,scaffold,False,OmegaDB(),{})
      xiParticles.append(xiParticle)
      # CONSIDER What to do with the rhoWeight.  Subtract off the
      # likelihood?  Subtract off the prior and the likelihood?  Do
      # nothing?  Subtracting off the likelihood makes
      # hmm-approx-filter.vnt from ppaml-cps/cp4/p3_hmm be
      # deterministic (except roundoff effects), but that may be an
      # artifact of the way that program is written.
      xiWeights.append(xiWeight - rhoWeight)
    return (xiParticles, xiWeights)

  def name(self): return "enumerative diversify"
