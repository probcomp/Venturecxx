from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..utils import sampleLogCategorical, cartesianProduct
from ..consistency import assertTrace, assertTorus
from mh import getCurrentValues, registerDeterministicLKernels

def getCartesianProductOfEnumeratedValues(trace,pnodes):
  enumeratedValues = [trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode)) for pnode in pnodes]
  return cartesianProduct(enumeratedValues)

class EnumerativeGibbsOperator(object):

  def compute_particles(self,trace,scaffold):
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
      xiParticle = self.copy_trace(trace)
      assertTorus(scaffold)
      registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
      xiParticles.append(xiParticle)
      xiWeights.append(regenAndAttach(xiParticle,scaffold,False,OmegaDB(),{}))
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
