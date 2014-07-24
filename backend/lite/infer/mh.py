def mixMH(trace,indexer,operator):
  start = time.time()
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
    accepted = True
  else:
#    sys.stdout.write("!")
    operator.reject() # May mutate trace
    accepted = False
  trace.recordProposal([operator.name()] + indexer.name(), time.time() - start, accepted)

class BlockScaffoldIndexer(object):
  def __init__(self,scope,block,interval=None):
    if scope == "default" and not (block == "all" or block == "one" or block == "ordered"):
        raise Exception("INFER default scope does not admit custom blocks (%r)" % block)
    self.scope = scope
    self.block = block
    self.interval = interval

  def sampleIndex(self,trace):
    if self.block == "one":
      self.true_block = trace.sampleBlock(self.scope)
      return constructScaffold(trace,[trace.getNodesInBlock(self.scope,self.true_block)])
    elif self.block == "all":
      return constructScaffold(trace,[trace.getAllNodesInScope(self.scope)])
    elif self.block == "ordered":
      return constructScaffold(trace,trace.getOrderedSetsInScope(self.scope))
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

  def name(self):
    return ["scaffold", self.scope, self.block] + ([self.interval] if self.interval is not None else []) + ([self.true_block] if hasattr(self, "true_block") else [])

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

#### Resampling from the prior

class MHOperator(InPlaceOperator):
  def propose(self, trace, scaffold):
    rhoWeight = self.prepare(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
    return trace, xiWeight - rhoWeight

  def name(self): return "resimulation MH"




