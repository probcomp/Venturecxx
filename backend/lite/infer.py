import random
import math
from consistency import assertTorus
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import Scaffold

def MHInfer(trace):
  import particle
  pnode = trace.samplePrincipalNode()
  rhoAux = trace.logDensityOfPrincipalNode(pnode)
  scaffold = Scaffold(trace,[pnode])
  rhoWeight,rhoDB = detachAndExtract(trace,scaffold.border,scaffold)
  assertTorus(scaffold)
  particle = particle.Particle(trace)
  xiWeight = regenAndAttach(particle,scaffold.border,scaffold,False,rhoDB,{})
  xiAux = particle.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) > (xiAux + xiWeight) - (rhoAux + rhoWeight): # reject
#    detachAndExtract(particle,scaffold.border,scaffold)
    scaffold.resetRegenCounts()
    regenAndAttach(trace,scaffold.border,scaffold,True,rhoDB,{})
  else: # accept
    particle.commit()
