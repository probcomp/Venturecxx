import random
import math
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..exception import VentureError
from mh import InPlaceOperator

class MissingEsrParentError(VentureError): pass
class NoSPRefError(VentureError): pass

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

  def name(self): return "rejection"
