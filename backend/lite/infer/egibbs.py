from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..lkernel import DeterministicLKernel
from ..utils import sampleLogCategorical, cartesianProduct
from ..consistency import assertTrace, assertTorus
from mh import getCurrentValues, registerDeterministicLKernels

def getCartesianProductOfEnumeratedValues(trace,pnodes):
  assert len(pnodes) > 0
  enumeratedValues = [trace.pspAt(pnode).enumerateValues(trace.argsAt(pnode)) for pnode in pnodes]
  assert len(enumeratedValues) > 0
  return cartesianProduct(enumeratedValues)

class EnumerativeGibbsOperator(object):

  def propose(self,trace,scaffold):
    from ..particle import Particle

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
  def name(self): return "enumerative gibbs"
