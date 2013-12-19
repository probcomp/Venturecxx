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
  scaffold = Scaffold(trace,[pnode])
  rhoWeight,rhoDB = detachAndExtract(trace,scaffold.border,scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border,scaffold,False,rhoDB,{})
  xiAux = trace.logDensityOfPrincipalNode(pnode)
  if math.log(random.random()) > (xiAux + xiWeight) - (rhoAux + rhoWeight): # reject
    detachAndExtract(trace,scaffold.border,scaffold)
    regenAndAttach(trace,scaffold.border,scaffold,True,rhoDB,{})
  else: pass # accept
