# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isApplicationNode
from venture.lite.node import isRequestNode
from venture.lite.node import isOutputNode
from venture.lite.omegadb import OmegaDB
from venture.lite.value import SPRef
from venture.lite.scope import isTagOutputPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.consistency import assertTorus, assertTrace

def detachAndExtract(trace, scaffold, compute_gradient = False):
  assertTrace(trace, scaffold)
  assert len(scaffold.border) == 1
  ans = detachAndExtractAtBorder(trace, scaffold.border[0], scaffold, compute_gradient=compute_gradient)
  assertTorus(scaffold)
  return ans

def detachAndExtractAtBorder(trace, border, scaffold, compute_gradient = False):
  """Returns the weight and an OmegaDB.  The OmegaDB contains
  sufficient information to restore the trace, and, if
  compute_gradient is True, to determine the partial derivative of
  the weight with respect to the value at each node.  The latter is
  computed by one level of reverse-mode AD, with the underlying trace
  serving as tape."""
  weight = 0
  omegaDB = OmegaDB()
  for node in reversed(border):
    if scaffold.isAbsorbing(node):
      weight += detach(trace, node, scaffold, omegaDB, compute_gradient)
    else:
      if node.isObservation: weight += getAndUnconstrain(trace,node)
      weight += extract(trace,node,scaffold,omegaDB, compute_gradient)
  return weight,omegaDB

def getAndUnconstrain(trace,node):
  return unconstrain(trace,trace.getConstrainableNode(node))

def unconstrain(trace,node):
  psp,args,value = trace.pspAt(node),trace.argsAt(node),trace.valueAt(node)
  trace.unregisterConstrainedChoice(node)
  psp.unincorporate(value,args)
  weight = psp.logDensity(value,args)
  psp.incorporate(value,args)
  return weight

def detach(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = unabsorb(trace, node, omegaDB, compute_gradient)
  weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  return weight

def unabsorb(trace, node, omegaDB, compute_gradient = False):
  # we need to pass groundValue here in case the return value is an SP
  # in which case the node would only contain an SPRef
  psp,args,gvalue = trace.pspAt(node),trace.argsAt(node),trace.groundValueAt(node)
  psp.unincorporate(gvalue,args)
  weight = psp.logDensity(gvalue,args)
  if compute_gradient:
    # Ignore the partial derivative of the value because the value is fixed
    (_, grad) = psp.gradientOfLogDensity(gvalue, args)
    omegaDB.addPartials(args.operandNodes + trace.esrParentsAt(node), grad)
  return weight

def extractParents(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  for parent in reversed(trace.definiteParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  return weight

def extractESRParents(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  for parent in reversed(trace.esrParentsAt(node)):
    weight += extract(trace, parent, scaffold, omegaDB, compute_gradient)
  return weight

def extract(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  weight += maybeExtractStaleAAA(trace, node, scaffold, omegaDB, compute_gradient)

  if scaffold.isResampling(node):
    trace.decRegenCountAt(scaffold,node)
    assert trace.regenCountAt(scaffold,node) >= 0
    if trace.regenCountAt(scaffold,node) == 0:
      if isApplicationNode(node):
        if isRequestNode(node):
          weight += unevalRequests(trace, node, scaffold, omegaDB, compute_gradient)
        weight += unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient)
      else:
        trace.setValueAt(node,None)
        assert isLookupNode(node) or isConstantNode(node)
        assert len(trace.parentsAt(node)) <= 1
        if compute_gradient:
          for p in trace.parentsAt(node):
            omegaDB.addPartial(p, omegaDB.getPartial(node)) # d/dx is 1 for a lookup node
      weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)

  return weight

def maybeExtractStaleAAA(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += extract(trace, value.makerNode, scaffold, omegaDB, compute_gradient)
  return weight

def unevalFamily(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = 0
  if isConstantNode(node): pass
  elif isLookupNode(node):
    assert len(trace.parentsAt(node)) == 1
    if compute_gradient:
      for p in trace.parentsAt(node):
        omegaDB.addPartial(p, omegaDB.getPartial(node)) # d/dx is 1 for a lookup node
    trace.disconnectLookup(node)
    trace.setValueAt(node,None)
    weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  else:
    assert isOutputNode(node)
    weight += unapply(trace, node, scaffold, omegaDB, compute_gradient)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace, operandNode, scaffold, omegaDB, compute_gradient)
    weight += unevalFamily(trace, node.operatorNode, scaffold, omegaDB, compute_gradient)
  return weight

def unapply(trace, node, scaffold, omegaDB, compute_gradient = False):
  weight = unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient)
  weight += extractESRParents(trace, node, scaffold, omegaDB, compute_gradient)
  weight += unevalRequests(trace, node.requestNode, scaffold, omegaDB, compute_gradient)
  weight += unapplyPSP(trace, node.requestNode, scaffold, omegaDB, compute_gradient)
  return weight

def teardownMadeSP(trace,node,isAAA):
  spRecord = trace.madeSPRecordAt(node)
  assert isinstance(spRecord,VentureSPRecord)
  assert len(spRecord.spFamilies.families) == 0
  trace.setValueAt(node,spRecord)
  if spRecord.sp.hasAEKernel(): trace.unregisterAEKernel(node)
  if isAAA:
    trace.registerAAAMadeSPAuxAt(node,trace.madeSPAuxAt(node))
  trace.setMadeSPRecordAt(node,None)

def unapplyPSP(trace, node, scaffold, omegaDB, compute_gradient = False):
  psp,args = trace.pspAt(node),trace.argsAt(node)
  if isTagOutputPSP(psp):
    scope,block = [trace.valueAt(n) for n in node.operandNodes[0:2]]
    blockNode = node.operandNodes[2]
    trace.unregisterRandomChoiceInScope(scope,block,blockNode)
  if psp.isRandom(): trace.unregisterRandomChoice(node)
  if isinstance(trace.valueAt(node),SPRef) and trace.valueAt(node).makerNode == node:
    teardownMadeSP(trace,node,scaffold.isAAA(node))

  weight = 0
  psp.unincorporate(trace.valueAt(node),args)
  if scaffold.hasLKernel(node):
    weight += scaffold.getLKernel(node).reverseWeight(trace,trace.valueAt(node),args)
    if compute_gradient:
      # TODO Should this take the whole args?  Should it take the esr parents into account?
      (partial, grad) = scaffold.getLKernel(node).gradientOfReverseWeight(trace, trace.valueAt(node), args)
      omegaDB.addPartial(node, partial)
      omegaDB.addPartials(args.operandNodes, grad)
  omegaDB.extractValue(node,trace.valueAt(node))

#  print "unapplyPSP",trace.valueAt(node)

  trace.setValueAt(node,None)
  if compute_gradient and any([scaffold.isResampling(p) or scaffold.isBrush(p) for p in trace.parentsAt(node)]) and not scaffold.hasLKernel(node):
    # Don't need to compute the simulation gradient if the parents are
    # not in the DRG or brush.
    # Not clear how to deal with LKernels.
    # - DeterministicLKernel is probably ok because the nodes they are applied at
    #   do not have interesting parents
    # - DeterministicMakerAAALKernel is probably ok because its gradientOfReverseWeight
    #   method computes the same thing gradientOfSimulate would properly have computed
    grad = psp.gradientOfSimulate(args, omegaDB.getValue(node), omegaDB.getPartial(node))
    omegaDB.addPartials(args.operandNodes + trace.esrParentsAt(node), grad)

  return weight

def unevalRequests(trace, node, scaffold, omegaDB, compute_gradient = False):
  assert isRequestNode(node)
  weight = 0
  request = trace.valueAt(node)
  # TODO I may have the following AD bug: if a request constructs an
  # expression which contains an embedded constant, the constant node
  # will not propagate the partial wrt that constant; and even if it
  # did, I wouldn't know how to backpropagate that partial through the
  # expression generator to the args.
  if request.lsrs and not omegaDB.hasLatentDB(trace.spAt(node)):
    omegaDB.registerLatentDB(trace.spAt(node),trace.spAt(node).constructLatentDB())

  for lsr in reversed(request.lsrs):
    weight += trace.spAt(node).detachLatents(trace.argsAt(node),lsr,omegaDB.getLatentDB(trace.spAt(node)))
    # TODO add gradient information for detached latents?

  for esr in reversed(request.esrs):
    esrParent = trace.popLastESRParent(node.outputNode)
    if trace.numRequestsAt(esrParent) == 0:
      trace.unregisterFamilyAt(node,esr.id)
      omegaDB.registerSPFamily(trace.spAt(node),esr.id,esrParent)
      weight += unevalFamily(trace, esrParent, scaffold, omegaDB, compute_gradient)

  return weight
