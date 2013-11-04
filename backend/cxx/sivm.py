from libtrace import Trace
import gc

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

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return self.directiveCounter

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()

    self.trace.eval(baseAddr,datum);
    self.trace.bindInGlobalEnv(id,baseAddr)

    self.directives[self.directiveCounter] = ["assume",id,datum]
    self.directivesToIDs[str(["assume",id,datum])] = self.directiveCounter

    return (self.directiveCounter,self.trace.extractValue(baseAddr))
    
  def predict(self,datum):
    baseAddr = self.nextBaseAddr()
    self.trace.eval(baseAddr,datum)

    self.directives[self.directiveCounter] = ["predict",datum]
    self.directivesToIDs[str(["predict",datum])] = self.directiveCounter

    return (self.directiveCounter,self.trace.extractValue(baseAddr))

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()
    self.trace.eval(baseAddr,datum)
    logDensity = self.trace.observe(baseAddr,val)

    # TODO check for -infinity? Throw an exception?
    if logDensity == float("-inf"): raise Exception("Cannot constrain!")
    self.directives[self.directiveCounter] = ["observe",datum,val]
    self.directivesToIDs[str(["observe",datum,val])] = self.directiveCounter

    return self.directiveCounter

  def findDirectiveID(self,directive):
    return self.directivesToIDs[str(directive)]

  def forget(self,directiveId):
    directive = self.directives[directiveId]
    if directive[0] == "assume": raise Exception("Cannot forget an ASSUME directive")
    if directive[0] == "observe": self.trace.unobserve(str(directiveID))
    self.trace.unevalFamily(str(directiveId))
    del self.directives[directiveId]

  def report_value(self,directiveId): return self.trace.getValue(str(directiveId))

  def clear(self): 
    del self.trace
    gc.collect()
    self.directiveCounter = 0
    self.directives = {}
    self.trace = Trace()

  def logscore(self): return self.trace.globalLogScore

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.trace.numRandomChoices }

  # This could be parameterized to call different inference programs.
  def infer(self,N=1):
    self.trace.infer(N)

  ### For Testing ###
  def loggingInfer(self,predictAddr,N=1,depth=1):
    predictions = []
    for n in range(N):
      (principalNode,ldRho) = self.trace.samplePrincipalNode()
      mhInfer(self.trace,depth)
      predictions.append(self.trace.extractValue())
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

