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

from venture.lite.sp import VentureSPRecord
from venture.lite.trace import Trace
from venture.lite.wttree import PMap
from venture.lite.wttree import PSet

class Particle(Trace):

  # The trace is expected to be a torus, with the chosen scaffold
  # already detached, or a particle.
  def __init__(self, trace):
    # Intentionally emulating algebraic data type
    # pylint: disable=unidiomatic-typecheck
    if type(trace) is Particle: self.initFromParticle(trace)
    elif type(trace) is Trace: self.initFromTrace(trace)
    else: raise Exception("Must init particle from trace or particle")

  # Note: using "copy()" informally for both legit_copy and persistent_copy
  def initFromParticle(self, particle):
    self.base = particle.base

    # (1) Persistent stuff
    self.rcs = particle.rcs
    self.ccs = particle.ccs
    self.aes = particle.aes

    self.values = particle.values
    self.madeSPs = particle.madeSPs

    self.scopes = particle.scopes # pmap => pmap => pset
    self.esrParents = particle.esrParents
    self.numRequests = particle.numRequests
    self.regenCounts = particle.regenCounts
    self.newMadeSPFamilies = particle.newMadeSPFamilies # pmap => pmap => node
    self.newChildren = particle.newChildren
    self.discardedAAAMakerNodes = particle.discardedAAAMakerNodes

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = { node : spaux.copy()
                        for node, spaux in particle.madeSPAuxs.iteritems() }

  def initFromTrace(self, trace):
    self.base = trace

    # (1) Persistent stuff
    self.rcs = PSet() # PSet Node
    self.ccs = PSet() # PSet Node
    self.aes = PSet() # PSet Node

    self.values = PMap()  # PMap Node VentureValue
    self.madeSPs = PMap() # PMap Node SP

    self.scopes = PMap()  # PMap scopeid (PMap blockid (PSet Node))
    # mutable list ok here b/c only touched by one particle
    self.esrParents = PMap() # PMap Node [Node]
    self.numRequests = PMap() # PMap Node Int
    self.regenCounts = PMap() # PMap Node int
    self.newMadeSPFamilies = PMap() # PMap Node (PMap id Node)
    self.newChildren = PMap() # PMap Node (PSet Node)
    self.discardedAAAMakerNodes = PSet() # PSet Node

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = {}


  ### Random choices and scopes

  def registerRandomChoice(self, node):
    self.rcs = self.rcs.insert(node)
    self.registerRandomChoiceInScope("default", node, node)

  def registerAEKernel(self, node):
    self.aes = self.aes.insert(node)

  def registerConstrainedChoice(self, node):
    self.ccs = self.ccs.insert(node)

  def unregisterRandomChoice(self, node): assert False

  def registerRandomChoiceInScope(self, scope, block, node):
    assert block is not None
    (scope, block) = self._normalizeEvaluatedScopeAndBlock(scope, block)
    if scope not in self.scopes:
      self.scopes = self.scopes.insert(scope, PMap())
    if block not in self.scopes.lookup(scope):
      def ins_b(blocks):
        return blocks.insert(block, PSet())
      self.scopes = self.scopes.adjust(scope, ins_b)
    def ins_n(blocks):
      return blocks.adjust(block, lambda pnodes: pnodes.insert(node))
    self.scopes = self.scopes.adjust(scope, ins_n)

  def unregisterRandomChoiceInScope(self, scope, block, node): assert False

  ### Misc

  def valueAt(self, node):
    if node in self.values: return self.values.lookup(node)
    else:
      return self.base.valueAt(node)

  def setValueAt(self, node, value):
    self.values = self.values.insert(node, value)

  def madeSPRecordAt(self, node):
    return VentureSPRecord(self.madeSPAt(node), self.madeSPAuxAt(node))

  def setMadeSPRecordAt(self, node, spRecord):
    self.madeSPs = self.madeSPs.insert(node, spRecord.sp)
    self.madeSPAuxs[node] = spRecord.spAux
    self.newMadeSPFamilies = self.newMadeSPFamilies.insert(node, PMap())

  def madeSPAt(self, node):
    if node in self.madeSPs: return self.madeSPs.lookup(node)
    else: return self.base.madeSPAt(node)

  def setMadeSPAt(self, node, sp):
    assert node not in self.madeSPs
    assert self.base.madeSPAt(node) is None
    self.madeSPs = self.madeSPs.insert(node, sp)

  def esrParentsAt(self, node):
    if node in self.esrParents: return self.esrParents.lookup(node)
    else: return self.base.esrParentsAt(node)

  def appendEsrParentAt(self, node, parent):
    assert not self.base.esrParentsAt(node)
    if node not in self.esrParents:
      self.esrParents = self.esrParents.insert(node, [])
    self.esrParents.lookup(node).append(parent)

  def regenCountAt(self, scaffold, node):
    assert self.base.regenCountAt(scaffold, node) == 0
    if node in self.regenCounts: return self.regenCounts.lookup(node)
    else: return self.base.regenCountAt(scaffold, node)

  def incRegenCountAt(self, scaffold, node):
    if node not in self.regenCounts:
      self.regenCounts = self.regenCounts.insert(node, 0)
    self.regenCounts = self.regenCounts.adjust(node, lambda rc: rc + 1)

  def incRequestsAt(self, node):
    if node not in self.numRequests:
      base_num_requests = self.base.numRequestsAt(node)
      self.numRequests = self.numRequests.insert(node, base_num_requests)
    self.numRequests = self.numRequests.adjust(node, lambda nr: nr + 1)

  def childrenAt(self, node):
    if node in self.newChildren:
      return self.base.childrenAt(node).union(self.newChildren.lookup(node))
    else:
      return self.base.childrenAt(node)

  def addChildAt(self, node, child):
    if node not in self.newChildren:
      self.newChildren = self.newChildren.insert(node, PSet())
    def ins(children):
      return children.insert(child)
    self.newChildren = self.newChildren.adjust(node, ins)

  def discardAAAMadeSPAuxAt(self, node):
    self.discardedAAAMakerNodes = self.discardedAAAMakerNodes.insert(node)

  def getAAAMadeSPAuxAt(self, node):
    if node in self.discardedAAAMakerNodes:
      return None
    else:
      return self.base.getAAAMadeSPAuxAt(node)

  ### SPFamilies

  def containsSPFamilyAt(self, node, id):
    makerNode = self.spRefAt(node).makerNode
    if makerNode in self.newMadeSPFamilies:
      assert isinstance(self.newMadeSPFamilies.lookup(makerNode), PMap)
      if id in self.newMadeSPFamilies.lookup(makerNode):
        return True
    elif self.base.madeSPFamiliesAt(makerNode).containsFamily(id): return True
    return False

  def initMadeSPFamiliesAt(self, node):
    assert node not in self.newMadeSPFamilies
    assert node.madeSPFamilies is None
    self.newMadeSPFamilies = self.newMadeSPFamilies.insert(node, PMap())

  def registerFamilyAt(self, node, esrId, esrParent):
    makerNode = self.spRefAt(node).makerNode
    if makerNode not in self.newMadeSPFamilies:
      self.newMadeSPFamilies = self.newMadeSPFamilies.insert(makerNode, PMap())
    def ins(ids):
      return ids.insert(esrId, esrParent)
    self.newMadeSPFamilies = self.newMadeSPFamilies.adjust(makerNode, ins)


  def madeSPFamilyAt(self, node, esrId):
    if node in self.newMadeSPFamilies and \
       esrId in self.newMadeSPFamilies.lookup(node):
      return self.newMadeSPFamilies.lookup(node).lookup(esrId)
    else:
      return self.base.madeSPFamilyAt(node, esrId)

  def spFamilyAt(self, node, esrId):
    makerNode = self.spRefAt(node).makerNode
    return self.madeSPFamilyAt(makerNode, esrId)

  ### Regular maps

  def madeSPAuxAt(self, node):
    if node not in self.madeSPAuxs:
      if self.base.madeSPAuxAt(node) is not None:
        self.madeSPAuxs[node] = self.base.madeSPAuxAt(node).copy()
      else: return None
    return self.madeSPAuxs[node]

  def setMadeSPAuxAt(self, node, aux):
    assert node not in self.madeSPAuxs
    assert self.base.madeSPAuxAt(node) is None
    self.madeSPAuxs[node] = aux

  ### Miscellaneous bookkeeping

  def numBlocksInScope(self, scope):
    # Why is this weird piece of code arranged like this?
    # Because in a custom scope, the number of blocks is given by the
    # number of `tag` invocations, regardless of whether the resulting
    # blocks have any unconstrained random choices.  In the default
    # scope, however, the number of "blocks" does depend on whether
    # random choices are constrained or not.
    # This place will need to be touched for Issue #421.
    if scope != "default":
      if scope in self.scopes:
        return len(self.scopes.lookup(scope)) + self.base.numBlocksInScope(scope)
      else:
        return self.base.numBlocksInScope(scope)
    actualUnconstrainedChoices = self.base.rcs.copy()
    for node in self.rcs: actualUnconstrainedChoices.add(node)
    for node in self.ccs: actualUnconstrainedChoices.remove(node)
    return len(actualUnconstrainedChoices)

  ### Commit

  def commit(self):
    # note that we do not call registerRandomChoice() because it in
    # turn calls registerRandomChoiceInScope()
    for node in self.rcs: self.base.rcs.add(node)

    # this iteration includes "default"
    for (scope, blocks) in self.scopes.iteritems():
      for (block, pnodes) in blocks.iteritems():
        for pnode in pnodes:
          self.base.registerRandomChoiceInScope(scope, block, pnode,
                                                unboxed=True)

    # note that we do not call registerConstrainedChoice() because it
    # in turn calls unregisterRandomChoice()
    for node in self.ccs: self.base.registerConstrainedChoice(node)

    for node in self.aes: self.base.registerAEKernel(node)

    for (node, value) in self.values.iteritems():
      self.base.setValueAt(node, value)

    for (node, madeSP) in self.madeSPs.iteritems():
      self.base.setMadeSPRecordAt(node, VentureSPRecord(madeSP))



    for (node, esrParents) in self.esrParents.iteritems():
      self.base.setEsrParentsAt(node, esrParents)
    for (node, numRequests) in self.numRequests.iteritems():
      self.base.setNumRequestsAt(node, numRequests)
    for (node, newMadeSPFamilies) in self.newMadeSPFamilies.iteritems():
      self.base.addNewMadeSPFamilies(node, newMadeSPFamilies)
    for (node, newChildren) in self.newChildren.iteritems():
      self.base.addNewChildren(node, newChildren)

    for (node, spaux) in self.madeSPAuxs.iteritems():
      self.base.setMadeSPAuxAt(node, spaux)

  # untested
  def transferRegenCounts(self, scaffold):
    for node in self.regenCounts:
      assert node in scaffold.regenCounts
      scaffold.regenCounts[node] = self.regenCounts.lookup(node)


  ### Methods that should never be called on particles

  def registerAAAMadeSPAuxAt(self, node, aux):
    raise Exception("Should not be called on a particle")

  def unregisterFamilyAt(self, node, esrId):
    raise Exception("Should not be called on a particle")

  def popEsrParentAt(self, node):
    raise Exception("Should not be called on a particle")

  def removeChildAt(self, node, child):
    raise Exception("Should not be called on a particle")

  def decRequestsAt(self, node):
    raise Exception("Should not be called on a particle")

  def unregisterAEKernel(self, node):
    raise Exception("Should not be called on a particle")

  def unregisterConstrainedChoice(self, node):
    raise Exception("Should not be called on a particle")

  def decRegenCountAt(self, scaffold, node):
    raise Exception("Should never be called on a particle")

  def numRequestsAt(self, node):
    raise Exception("Should not be called on a particle")
