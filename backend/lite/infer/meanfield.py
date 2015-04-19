# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from mh import MHOperator
from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..node import ApplicationNode, Args
from ..lkernel import VariationalLKernel

def registerVariationalLKernels(trace,scaffold):
  hasVariational = False
  for node in scaffold.regenCounts:
    if isinstance(node,ApplicationNode) and \
       not trace.isConstrainedAt(node) and \
       trace.pspAt(node).hasVariationalLKernel() and \
       not scaffold.isResampling(node.operatorNode):
      scaffold.lkernels[node] = trace.pspAt(node).getVariationalLKernel(Args(trace,node))
      hasVariational = True
  return hasVariational

class MeanfieldOperator(object):
  def __init__(self,numIters,stepSize):
    self.numIters = numIters
    self.stepSize = stepSize
    self.delegate = None

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold
    if not registerVariationalLKernels(trace,scaffold):
      self.delegate = MHOperator()
      return self.delegate.propose(trace,scaffold)
    _,self.rhoDB = detachAndExtract(trace,scaffold)

    for _ in range(self.numIters):
      gradients = {}
      gain = regenAndAttach(trace,scaffold,False,OmegaDB(),gradients)
      detachAndExtract(trace,scaffold)
      for node,lkernel in scaffold.lkernels.iteritems():
        if isinstance(lkernel,VariationalLKernel):
          assert node in gradients
          lkernel.updateParameters(gradients[node],gain,self.stepSize)

    rhoWeight = regenAndAttach(trace,scaffold,True,self.rhoDB,{})
    detachAndExtract(trace,scaffold)

    xiWeight = regenAndAttach(trace,scaffold,False,OmegaDB(),{})
    return trace,xiWeight - rhoWeight

  def accept(self):
    if self.delegate is None:
      pass
    else:
      self.delegate.accept()

  def reject(self):
    # TODO This is the same as MHOperator reject except for the
    # delegation thing -- abstract
    if self.delegate is None:
      detachAndExtract(self.trace,self.scaffold)
      regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})
    else:
      self.delegate.reject()

  def name(self): return "meanfield"
