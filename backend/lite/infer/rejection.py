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
      return scaffold.getLKernel(node).weightBound(trace, value, args)
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
  def __init__(self, trials):
    super(RejectionOperator, self).__init__()
    self.trials = trials

  def propose(self, trace, scaffold):
    self.prepare(trace, scaffold)
    logBound = computeRejectionBound(trace, scaffold, scaffold.border[0])
    accept = False
    attempt = 0
    while not accept and (self.trials is None or self.trials > attempt):
      xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
      accept = random.random() < math.exp(xiWeight - logBound)
      if not accept:
        detachAndExtract(trace, scaffold)
        attempt += 1
    if not accept:
      # Ran out of attempts
      print "Warning: rejection hit attempt bound of %s" % self.trials
      regenAndAttach(trace, scaffold, True, self.rhoDB, {})
    return trace, 0

  def name(self): return "rejection"

class BogoPossibilizeOperator(InPlaceOperator):
  """Find a possible state by rejection.

If the start state is already possible, don't move."""

  def propose(self, trace, scaffold):
    while True:
      rhoWeight = self.prepare(trace, scaffold)
      xiWeight = regenAndAttach(trace, scaffold, False, self.rhoDB, {})
      if rhoWeight > float("-inf"):
        # The original state was possible; force rejecting the
        # transition
        return trace, float("-inf")
      elif xiWeight > float("-inf"):
        # The original state was impossible, and the new state is
        # possible; force accepting the transition
        return trace, float("+inf")
      else:
        self.reject() # To restore everything to its proper state TODO use particles?

  def name(self): return "bogo_possibilize"
