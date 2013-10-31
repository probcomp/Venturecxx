from trace import *
from regen import *
from parse import parse
from address import *
from primitives import *
from constructDRG import *
from detach import *
from infer import *
from render import renderTrace
import gc
import sys

# Our SIVM is not a fully conforming SIVM, for reasons I hope
# the person reading this will understand better than I do.
# For one, the directives take strings and does the parsing,
# which can easily be changed. Venture also has some kind of
# type system which this does not support explicitly.

# A note on addresses: addresses are lists (though they are 
# also converted to strings before hashing), and the definite
# families begin with [<directiveId>]. 

# Suppose the SP created at address SP-ADDR requests an LIA
# with local address LIA-ADDR. Then the full address of that LIA 
# would be SP-ADDR + [<sp>] + LIA-NAME (where + is append).


class SIVM:

  def __init__(self):
    self.directiveCounter = 0
    self.directives = {}
    self.directivesToIDs = {}
    self.trace = Trace()
    addPrimitives(self.trace)
    addEnvironments(self.trace)

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return makePrimitiveAddress(str(self.directiveCounter))

  def globalEnv(self): 
    return self.trace.getNode(globalEnvAddr()).getValue()

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()
    evalFamily(self.trace,baseAddr,datum,self.globalEnv(),DRG(),False,{},{},{})
    self.globalEnv().update({id:baseAddr})
    self.directives[self.directiveCounter] = ["assume",id,datum]
    self.directivesToIDs[str(["assume",id,datum])] = self.directiveCounter
    self.trace.getNode(baseAddr).isDefiniteRoot = True
    self.trace.getNode(baseAddr).symbolName = id
    return (self.directiveCounter,self.trace.getNode(baseAddr).getValue())

    
  def predict(self,datum):
    baseAddr = self.nextBaseAddr()
    evalFamily(self.trace,baseAddr,datum,self.globalEnv(),DRG(),False,{},{},{})
    self.directives[self.directiveCounter] = ["predict",datum]
    self.directivesToIDs[str(["predict",datum])] = self.directiveCounter
    self.trace.getNode(baseAddr).isDefiniteRoot = True
    return (self.directiveCounter,self.trace.getNode(baseAddr).getValue())

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()
    evalFamily(self.trace,baseAddr,datum,self.globalEnv(),DRG(),False,{},{},{})
    node = self.trace.getNode(baseAddr)
    node.setObservedValue(val)
    # TODO check for -infinity? Throw an exception?
    logDensity = constrain(self.trace,node,val)
    if logDensity == float("-inf"): raise Exception("Cannot constrain!")
    self.directives[self.directiveCounter] = ["observe",datum,val]
    self.directivesToIDs[str(["observe",datum,val])] = self.directiveCounter
    self.trace.getNode(baseAddr).isDefiniteRoot = True
    return self.directiveCounter

  def findDirectiveID(self,directive):
    return self.directivesToIDs[str(directive)]

  def forget(self,directiveId):
    directive = self.directives[directiveId]
    if directive[0] == "assume": raise Exception("Cannot forget an ASSUME directive")
    root = trace.getNode(makePrimitiveAddress(str(directiveId)))
    if directive[0] == "observe": unconstrain(self.trace,root)
    unevalFamily(self.trace,root,DRG(),{})
    del self.directives[directiveId]

  def report_value(self,directiveId): return self.trace.getNode(makePrimitiveAddress(str(directiveId))).getValue()

  def clear(self): 
    del self.trace
    # TODO we can actually destroy all the nodes when destroying the trace,
    # but not sure how to do that in Python yet.
    gc.collect()
    self.directiveCounter = 0
    self.directives = {}
    self.trace = Trace()
    addPrimitives(self.trace)
    addEnvironments(self.trace)

  def logscore(self): return self.trace.globalLogScore

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.trace.numRandomChoices }

  # This could be parameterized to call different inference programs.
  def infer(self,N=1,depth=1): 
    for n in range(N):
      # TODO passing self only for debugging
      mhInfer(self.trace,depth,self)

  ### For Testing ###
  def loggingInfer(self,predictAddr,N=1,depth=1):
    predictions = []
    for n in range(N):
      (principalNode,ldRho) = self.trace.samplePrincipalNode()
      mhInfer(self.trace,depth)
      predictions.append(self.trace.getNode(predictAddr).getValue())
    return predictions

  def loggingPGibbsInfer(self,predictAddr,N=1,P=1,T=1,depth=1):
    predictions = []
    for n in range(N):
      pGibbsInfer(self.trace,P,T,depth)
      predictions.append(self.trace.getNode(predictAddr).getValue())
    return predictions

  def loggingMeanFieldInfer(self,predictAddr,N=1):
    predictions = []
    for n in range(N):
#      sys.stdout.write('.')
      meanFieldInfer(self.trace)
      predictions.append(self.trace.getNode(predictAddr).getValue())
    return predictions

