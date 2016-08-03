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

import copy
import math
import random

from collections import OrderedDict

import numpy.random as npr
from numpy.testing import assert_allclose

from venture.exception import VentureException
from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.builtin import builtInSPs
from venture.lite.builtin import builtInValues
from venture.lite.detach import detachAndExtract
from venture.lite.detach import unconstrain
from venture.lite.detach import unevalFamily
from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError
from venture.lite.infer import BlockScaffoldIndexer
from venture.lite.lkernel import DeterministicLKernel
from venture.lite.node import ConstantNode
from venture.lite.node import LookupNode
from venture.lite.node import OutputNode
from venture.lite.node import RequestNode
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.node import TraceNodeArgs
from venture.lite.omegadb import OmegaDB
from venture.lite.orderedset import OrderedSet
from venture.lite.psp import ESRRefOutputPSP
from venture.lite.regen import constrain
from venture.lite.regen import evalFamily
from venture.lite.regen import processMadeSP
from venture.lite.regen import regenAndAttach
from venture.lite.regen import restore
from venture.lite.scaffold import Scaffold
from venture.lite.scaffold import constructScaffold
from venture.lite.scope import isTagExcludeOutputPSP
from venture.lite.scope import isTagOutputPSP
from venture.lite.serialize import OrderedOmegaDB
from venture.lite.smap import SamplableMap
from venture.lite.sp import SPFamilies
from venture.lite.sp import VentureSPRecord
from venture.lite.types import ExpressionType
from venture.lite.value import SPRef
from venture.lite.value import VenturePair
from venture.lite.value import VentureSymbol
from venture.lite.value import VentureValue
import venture.lite.infer as infer

class Trace(object):
  def __init__(self, seed):

    self.globalEnv = VentureEnvironment()
    for name, val in builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

    self.rcs = OrderedSet()
    self.ccs = OrderedSet()
    self.aes = OrderedSet()
    self.unpropagatedObservations = OrderedDict() # {node:val}
    self.families = OrderedDict()
    self.scopes = OrderedDict() # :: {scope-name:smap{block-id:set(node)}}

    self.profiling_enabled = False
    self.stats = []

    assert seed is not None
    rng = random.Random(seed)
    self.np_rng = npr.RandomState(rng.randint(1, 2**31 - 1))
    self.py_rng = random.Random(rng.randint(1, 2**31 - 1))

  def scope_keys(self):
    # A hack for allowing scope names not to be quoted in inference
    # programs (needs to be a method so Puma can implement it)
    return self.scopes.keys()

  def sealEnvironment(self):
    self.globalEnv = VentureEnvironment(self.globalEnv)

  def bindPrimitiveName(self, name, val):
    address = ('primitive name', name)
    self.globalEnv.addBinding(name, self.createConstantNode(address, val))

  def bindPrimitiveSP(self, name, sp):
    address = ('primitive SP', name)
    spNode = self.createConstantNode(address, VentureSPRecord(sp))
    processMadeSP(self, spNode, False)
    assert isinstance(self.valueAt(spNode), SPRef)
    self.globalEnv.addBinding(name, spNode)

  def registerAEKernel(self, node): self.aes.add(node)
  def unregisterAEKernel(self, node): self.aes.remove(node)

  def registerRandomChoice(self, node):
    assert node not in self.rcs
    self.rcs.add(node)
    self.registerRandomChoiceInScope("default", node, node)

  def registerRandomChoiceInScope(self, scope, block, node, unboxed=False):
    if not unboxed: (scope, block) = self._normalizeEvaluatedScopeAndBlock(scope, block)
    if scope not in self.scopes: self.scopes[scope] = SamplableMap()
    if block not in self.scopes[scope]: self.scopes[scope][block] = OrderedSet()
    assert node not in self.scopes[scope][block]
    self.scopes[scope][block].add(node)
    assert scope != "default" or len(self.scopes[scope][block]) == 1

  def unregisterRandomChoice(self, node):
    assert node in self.rcs
    self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default", node, node)

  def unregisterRandomChoiceInScope(self, scope, block, node):
    (scope, block) = self._normalizeEvaluatedScopeAndBlock(scope, block)
    self.scopes[scope][block].remove(node)
    if scope == "default":
      assert len(self.scopes[scope][block]) == 0
    if len(self.scopes[scope][block]) == 0: del self.scopes[scope][block]
    if len(self.scopes[scope]) == 0 and (scope != "default"): del self.scopes[scope]

  def _normalizeEvaluatedScopeOrBlock(self, val):
    if isinstance(val, VentureSymbol):
      if val.getSymbol() in ["default", "none", "one", "all", "each", "ordered"]:
        return val.getSymbol()
    elif isinstance(val, VenturePair):
      if isinstance(val.first, VentureSymbol) and \
         val.first.getSymbol() == 'ordered_range':
        return ['ordered_range', val.rest.first, val.rest.rest.first]
    return val

  # [FIXME] repetitive, but not sure why these exist at all
  def _normalizeEvaluatedScope(self, scope):
    return self._normalizeEvaluatedScopeOrBlock(scope)

  def _normalizeEvaluatedScopeAndBlock(self, scope, block):
    #import pdb; pdb.set_trace()
    if scope == "default":
      #assert isinstance(block, Node)
      return (scope, block)
    else:
      #assert isinstance(scope, VentureValue)
      #assert isinstance(block, VentureValue)

      scope = self._normalizeEvaluatedScopeOrBlock(scope)
      block = self._normalizeEvaluatedScopeOrBlock(block)

      return (scope, block)

  def registerConstrainedChoice(self, node):
    if node in self.ccs:
      raise VentureException("evaluation", "Cannot constrain the same random choice twice.", address = node.address)
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def unregisterConstrainedChoice(self, node):
    assert node in self.ccs
    self.ccs.remove(node)
    if self.pspAt(node).isRandom(): self.registerRandomChoice(node)

  def createConstantNode(self, address, val): return ConstantNode(address, val)
  def createLookupNode(self, address, sourceNode):
    lookupNode = LookupNode(address, sourceNode)
    self.setValueAt(lookupNode, self.valueAt(sourceNode))
    self.addChildAt(sourceNode, lookupNode)
    return lookupNode

  def createApplicationNodes(self, address, operatorNode, operandNodes, env):
    requestNode = RequestNode(address, operatorNode, operandNodes, env)
    outputNode = OutputNode(address, operatorNode, operandNodes, requestNode, env)
    self.addChildAt(operatorNode, requestNode)
    self.addChildAt(operatorNode, outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode, requestNode)
      self.addChildAt(operandNode, outputNode)
    requestNode.registerOutputNode(outputNode)
    return (requestNode, outputNode)

  def addESREdge(self, esrParent, outputNode):
    self.incRequestsAt(esrParent)
    self.addChildAt(esrParent, outputNode)
    self.appendEsrParentAt(outputNode, esrParent)

  def popLastESRParent(self, outputNode):
    assert self.esrParentsAt(outputNode)
    esrParent = self.popEsrParentAt(outputNode)
    self.removeChildAt(esrParent, outputNode)
    self.decRequestsAt(esrParent)
    return esrParent

  def disconnectLookup(self, lookupNode):
    self.removeChildAt(lookupNode.sourceNode, lookupNode)

  def reconnectLookup(self, lookupNode):
    self.addChildAt(lookupNode.sourceNode, lookupNode)

  def groundValueAt(self, node):
    value = self.valueAt(node)
    if isinstance(value, SPRef): return self.madeSPRecordAt(value.makerNode)
    else: return value

  def argsAt(self, node): return TraceNodeArgs(self, node)

  def spRefAt(self, node):
    candidate = self.valueAt(node.operatorNode)
    if not isinstance(candidate, SPRef):
      raise infer.NoSPRefError("Cannot apply a non-procedure: %s (at node %s with operator %s)" % (candidate, node, node.operatorNode))
    assert isinstance(candidate, SPRef)
    return candidate

  def spAt(self, node): return self.madeSPAt(self.spRefAt(node).makerNode)
  def spFamiliesAt(self, node):
    spFamilies = self.madeSPFamiliesAt(self.spRefAt(node).makerNode)
    assert isinstance(spFamilies, SPFamilies)
    return spFamilies
  def spauxAt(self, node): return self.madeSPAuxAt(self.spRefAt(node).makerNode)
  def pspAt(self, node): return node.relevantPSP(self.spAt(node))

  #### Stuff that a particle trace would need to override for persistence

  def valueAt(self, node):
    return node.value

  def setValueAt(self, node, value):
    assert node.isAppropriateValue(value)
    node.value = value

  def madeSPRecordAt(self, node):
    assert node.madeSPRecord is not None
    return node.madeSPRecord

  def setMadeSPRecordAt(self, node, spRecord):
    node.madeSPRecord = spRecord

  def madeSPAt(self, node): return self.madeSPRecordAt(node).sp
  def setMadeSPAt(self, node, sp):
    spRecord = self.madeSPRecordAt(node)
    spRecord.sp = sp

  def madeSPFamiliesAt(self, node): return self.madeSPRecordAt(node).spFamilies
  def setMadeSPFamiliesAt(self, node, families):
    spRecord = self.madeSPRecordAt(node)
    spRecord.spFamilies = families

  def madeSPAuxAt(self, node): return self.madeSPRecordAt(node).spAux
  def setMadeSPAuxAt(self, node, aux):
    spRecord = self.madeSPRecordAt(node)
    spRecord.spAux = aux

  def getAAAMadeSPAuxAt(self, node): return node.aaaMadeSPAux
  def discardAAAMadeSPAuxAt(self, node):
    node.aaaMadeSPAux = None
  def registerAAAMadeSPAuxAt(self, node, aux):
    node.aaaMadeSPAux = aux

  def parentsAt(self, node): return node.parents()
  def definiteParentsAt(self, node): return node.definiteParents()

  def esrParentsAt(self, node): return node.esrParents
  def setEsrParentsAt(self, node, parents): node.esrParents = parents
  def appendEsrParentAt(self, node, parent): node.esrParents.append(parent)
  def popEsrParentAt(self, node): return node.esrParents.pop()

  def childrenAt(self, node): return node.children
  def setChildrenAt(self, node, children): node.children = children
  def addChildAt(self, node, child): node.children.add(child)
  def removeChildAt(self, node, child): node.children.remove(child)

  def registerFamilyAt(self, node, esrId, esrParent): self.spFamiliesAt(node).registerFamily(esrId, esrParent)
  def unregisterFamilyAt(self, node, esrId): self.spFamiliesAt(node).unregisterFamily(esrId)
  def containsSPFamilyAt(self, node, esrId): return self.spFamiliesAt(node).containsFamily(esrId)
  def spFamilyAt(self, node, esrId): return self.spFamiliesAt(node).getFamily(esrId)
  def madeSPFamilyAt(self, node, esrId): return self.madeSPFamiliesAt(node).getFamily(esrId)

  def initMadeSPFamiliesAt(self, node): self.setMadeSPFamiliesAt(node, SPFamilies())
  def clearMadeSPFamiliesAt(self, node): self.setMadeSPFamiliesAt(node, None)

  def numRequestsAt(self, node): return node.numRequests
  def setNumRequestsAt(self, node, num): node.numRequests = num
  def incRequestsAt(self, node): node.numRequests += 1
  def decRequestsAt(self, node): node.numRequests -= 1

  def regenCountAt(self, scaffold, node): return scaffold.regenCounts[node]
  def incRegenCountAt(self, scaffold, node): scaffold.regenCounts[node] += 1
  def decRegenCountAt(self, scaffold, node): scaffold.regenCounts[node] -= 1 # need not be overriden

  def isConstrainedAt(self, node): return node in self.ccs

  #### For kernels
  def getScope(self, scope):
    scope = self._normalizeEvaluatedScopeOrBlock(scope)
    if scope in self.scopes:
      return self.scopes[scope]
    else:
      return SamplableMap()

  def sampleBlock(self, scope): return self.getScope(scope).sample(self.py_rng)[0]
  def logDensityOfBlock(self, scope): return -1 * math.log(self.numBlocksInScope(scope))
  def blocksInScope(self, scope): return self.getScope(scope).keys()
  def numBlocksInScope(self, scope): return len(self.getScope(scope).keys())

  def getAllNodesInScope(self, scope):
    blocks = [self.getNodesInBlock(scope, block) for block in self.getScope(scope).keys()]
    if len(blocks) == 0: # Guido, WTF?
      return OrderedSet()
    else:
      return OrderedSet.union(*blocks)

  def getOrderedSetsInScope(self, scope, interval=None):
    if interval is None:
      return [self.getNodesInBlock(scope, block) for block in sorted(self.getScope(scope).keys())]
    else:
      blocks = [b for b in self.getScope(scope).keys() if b >= interval[0] if b <= interval[1]]
      return [self.getNodesInBlock(scope, block) for block in sorted(blocks)]

  def numNodesInBlock(self, scope, block): return len(self.getNodesInBlock(scope, block))

  def getNodesInBlock(self, scope, block):
    #import pdb; pdb.set_trace()
    #scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    nodes = self.scopes[scope][block]
    if scope == "default":
      return nodes
    else:
      return self.randomChoicesInExtent(nodes, scope, block)

  def randomChoicesInExtent(self, nodes, scope, block):
    # The scope and block, if present, limit the computed dynamic
    # extent to everything that is not explicitly excluded from them.
    pnodes = OrderedSet()
    for node in nodes: self.addRandomChoicesInExtent(node, scope, block, pnodes)
    return pnodes

  def addRandomChoicesInExtent(self, node, scope, block, pnodes):
    if not isOutputNode(node): return

    if self.pspAt(node).isRandom() and node not in self.ccs: pnodes.add(node)

    requestNode = node.requestNode
    if self.pspAt(requestNode).isRandom() and requestNode not in self.ccs: pnodes.add(requestNode)

    for esr in self.valueAt(node.requestNode).esrs:
      self.addRandomChoicesInExtent(self.spFamilyAt(requestNode, esr.id), scope, block, pnodes)

    self.addRandomChoicesInExtent(node.operatorNode, scope, block, pnodes)

    for i, operandNode in enumerate(node.operandNodes):
      if i == 2 and isTagOutputPSP(self.pspAt(node)):
        (new_scope, new_block, _) = [self.valueAt(randNode) for randNode in node.operandNodes]
        (new_scope, new_block) = self._normalizeEvaluatedScopeAndBlock(new_scope, new_block)
        if scope != new_scope or block == new_block: self.addRandomChoicesInExtent(operandNode, scope, block, pnodes)
      elif i == 1 and isTagExcludeOutputPSP(self.pspAt(node)):
        (excluded_scope, _) = [self.valueAt(randNode) for randNode in node.operandNodes]
        excluded_scope = self._normalizeEvaluatedScope(excluded_scope)
        if scope != excluded_scope: self.addRandomChoicesInExtent(operandNode, scope, block, pnodes)
      else:
        self.addRandomChoicesInExtent(operandNode, scope, block, pnodes)


  def scopeHasEntropy(self, scope):
    # right now scope in self.scopes iff it has entropy
    return self.numBlocksInScope(scope) > 0

  def recordProposal(self, **kwargs):
    if self.profiling_enabled:
      self.stats.append(kwargs)

  #### External interface to engine.py
  def eval(self, id, exp):
    assert id not in self.families
    (_, self.families[id]) = evalFamily(
      self, Address(List(id)), self.unboxExpression(exp), self.globalEnv,
      Scaffold(), False, OmegaDB(), OrderedDict())

  def bindInGlobalEnv(self, sym, id):
    try:
      self.globalEnv.addBinding(sym, self.families[id])
    except VentureError as e:
      raise VentureException("invalid_argument", message=e.message,
                             argument="symbol")

  def unbindInGlobalEnv(self, sym): self.globalEnv.removeBinding(sym)

  def boundInGlobalEnv(self, sym): return self.globalEnv.symbolBound(sym)

  def extractValue(self, id): return self.boxValue(self.valueAt(self.families[id]))

  def extractRaw(self, id): return self.valueAt(self.families[id])

  def observe(self, id, val):
    node = self.families[id]
    self.unpropagatedObservations[node] = self.unboxValue(val)

  def makeConsistent(self):
    weight = 0
    for node, val in self.unpropagatedObservations.iteritems():
      appNode = self.getConstrainableNode(node)
#      print "PROPAGATE", node, appNode
      scaffold = constructScaffold(self, [OrderedSet([appNode])])
      rhoWeight, _ = detachAndExtract(self, scaffold)
      scaffold.lkernels[appNode] = DeterministicLKernel(self.pspAt(appNode), val)
      xiWeight = regenAndAttach(self, scaffold, False, OmegaDB(), OrderedDict())
      # If xiWeight is -inf, we are in an impossible state, but that might be ok.
      # Finish constraining, to avoid downstream invariant violations.
      node.observe(val)
      constrain(self, appNode, node.observedValue)
      weight += xiWeight
      weight -= rhoWeight
    self.unpropagatedObservations.clear()
    if not math.isinf(weight) and not math.isnan(weight):
      return weight
    else:
      # If one observation made the state inconsistent, the rhoWeight
      # of another might conceivably be infinite, possibly leading to
      # a nan weight.  I want to normalize these to indicating that
      # the resulting state is impossible.
      return float("-inf")

  # use instead of makeConsistent when restoring a trace
  def registerConstraints(self):
    for node, val in self.unpropagatedObservations.iteritems():
      appNode = self.getConstrainableNode(node)
      #import ipdb; ipdb.set_trace()
      node.observe(val)
      constrain(self, appNode, node.observedValue)
    self.unpropagatedObservations.clear()

  def getConstrainableNode(self, node):
    candidate = self.getOutermostNonReferenceNode(node)
    if isConstantNode(candidate):
      raise VentureException("evaluation", "Cannot constrain a constant value.",
                             address = node.address)
    if not self.pspAt(candidate).isRandom():
      raise VentureException("evaluation", "Cannot constrain a deterministic value.",
                             address = node.address)
    return candidate

  def getOutermostNonReferenceNode(self, node):
    if isConstantNode(node): return node
    if isLookupNode(node): return self.getOutermostNonReferenceNode(node.sourceNode)
    assert isOutputNode(node)
    if isinstance(self.pspAt(node), ESRRefOutputPSP):
      if self.esrParentsAt(node):
        return self.getOutermostNonReferenceNode(self.esrParentsAt(node)[0])
      else:
        # Could happen if this method is called on a torus, e.g. for rejection sampling
        raise infer.MissingEsrParentError()
    elif isTagOutputPSP(self.pspAt(node)):
      return self.getOutermostNonReferenceNode(node.operandNodes[2])
    else: return node

  def unobserve(self, id):
    node = self.families[id]
    appNode = self.getConstrainableNode(node)
    if node.isObservation:
      weight = unconstrain(self, appNode)
      node.isObservation = False
    else:
      assert node in self.unpropagatedObservations
      del self.unpropagatedObservations[node]
      weight = 0
    return weight

  def uneval(self, id):
    assert id in self.families
    unevalFamily(self, self.families[id], Scaffold(), OmegaDB())
    del self.families[id]

  def numRandomChoices(self):
    return len(self.rcs)

  # XXX Why are all these inference operations defined as trace methods?
  # Because
  # - Multiprocessing doesn't know how to call raw functions, and
  #   currently uses a Trace as the object whose methods to invoke
  # - We didn't learn how to export raw functions from the C++
  #   extension, but we want to show the same interface to Traces.
  def primitive_infer(self, exp):
    return infer.primitive_infer(self, exp)

  # XXX Why is there this weird structure of some methods forwarding
  # to definite functions and other things indirecting through the
  # primitive_infer dispatch?  History: primitive_infer used not to
  # return values.  Also ambiguity: not clear which style is better.
  def log_likelihood_at(self, *args):
    return infer.log_likelihood_at(self, args)

  def log_joint_at(self, *args):
    return infer.log_joint_at(self, args)

  def likelihood_weight(self):
    # TODO This is a different control path from primitive_infer
    # because it needs to return the weight, and that didn't used to
    # return values when this was writen.
    scaffold = BlockScaffoldIndexer("default", "all").sampleIndex(self)
    (_rhoWeight, rhoDB) = detachAndExtract(self, scaffold)
    xiWeight = regenAndAttach(self, scaffold, False, rhoDB, OrderedDict())
    # Always "accept"
    return xiWeight

  def freeze(self, id):
    assert id in self.families
    node = self.families[id]
    if isConstantNode(node):
      # All set
      pass
    else:
      assert isOutputNode(node)
      value = self.valueAt(node)
      unevalFamily(self, node, Scaffold(), OmegaDB())
      # XXX It looks like we kinda want to replace the identity of this
      # node by a constant node, but we don't have a nice way to do that
      # so we fake it by dropping the components and marking it frozen.
      node.isFrozen = True
      self.setValueAt(node, value)
      node.requestNode = None
      node.operandNodes = None
      node.operatorNode = None

  def diversify(self, exp, copy_trace):
    """Return the pair of parallel lists of traces and weights that
results from applying the given expression as a diversification
operator.  Duplicate self if necessary with the provided copy_trace
function.

    """
    assert len(exp) >= 3
    (operator, scope, block) = exp[0:3]
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    if not self.scopeHasEntropy(scope):
      return ([self], [0.0])
    if operator == "enumerative":
      return infer.EnumerativeDiversify(copy_trace)(self, BlockScaffoldIndexer(scope, block))
    else: raise Exception("DIVERSIFY %s is not implemented" % operator)

  def select(self, scope, block=None):
    if block is not None:
      # Assume old scope-block argument style
      scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
      return BlockScaffoldIndexer(scope, block).sampleIndex(self)
    else:
      # Assume new subproblem-selector argument style
      selection_blob = scope
      from venture.untraced.trace_search import TraceSearchIndexer
      return TraceSearchIndexer(selection_blob.datum).sampleIndex(self)

  def just_detach(self, scaffold):
    return detachAndExtract(self, scaffold)

  def just_regen(self, scaffold):
    return regenAndAttach(self, scaffold, False, OmegaDB(), OrderedDict())

  def just_restore(self, scaffold, rhoDB):
    return regenAndAttach(self, scaffold, True, rhoDB, OrderedDict())

  def detach_for_proposal(self, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    from infer.mh import getCurrentValues, registerDeterministicLKernels, unregisterDeterministicLKernels
    currentValues = getCurrentValues(self, pnodes)
    registerDeterministicLKernels(self, scaffold, pnodes, currentValues)
    rhoWeight, rhoDB = detachAndExtract(self, scaffold)
    unregisterDeterministicLKernels(self, scaffold, pnodes) # de-mutate the scaffold in case it is used for subsequent operations
    return rhoWeight, rhoDB

  def regen_with_proposal(self, scaffold, values):
    pnodes = scaffold.getPrincipalNodes()
    assert len(values) == len(pnodes), "Tried to propose %d values, but subproblem accepts %d values" % (len(values), len(pnodes))
    from infer.mh import registerDeterministicLKernels, unregisterDeterministicLKernels
    registerDeterministicLKernels(self, scaffold, pnodes, values)
    xiWeight = regenAndAttach(self, scaffold, False, OmegaDB(), OrderedDict())
    # de-mutate the scaffold in case it is used for subsequent operations
    unregisterDeterministicLKernels(self, scaffold, pnodes)
    return xiWeight

  def checkInvariants(self):
    # print "Begin invariant check"
    assert len(self.unpropagatedObservations) == 0, \
      "Don't checkInvariants with unpropagated observations"
    rcs = copy.copy(self.rcs)
    ccs = copy.copy(self.ccs)
    aes = copy.copy(self.aes)
    scopes = OrderedDict()
    for (scope_name, scope) in self.scopes.iteritems():
      new_scope = SamplableMap()
      for (block_name, block) in scope.iteritems():
        new_scope[block_name] = copy.copy(block)
      scopes[scope_name] = new_scope

    scaffold = BlockScaffoldIndexer("default", "all").sampleIndex(self)
    rhoWeight, rhoDB = detachAndExtract(self, scaffold)

    assert len(self.rcs) == 0, "Global detach left random choices registered"
    # TODO What if an observed random choice had registered an
    # AEKernel?  Will that be left here?
    assert len(self.aes) == 0, "Global detach left AEKernels registered"
    assert len(self.scopes) == 1, "Global detach left random choices in non-default scope %s" % self.scopes
    assert len(self.scopes['default']) == 0, "Global detach left random choices in default scope %s" % self.scopes['default']

    xiWeight = regenAndAttach(self, scaffold, True, rhoDB, OrderedDict())

    # XXX Apparently detach/regen sometimes has the effect of changing
    # the order of rcs.
    assert set(rcs) == set(self.rcs), "Global detach/restore changed the registered random choices from %s to %s" % (rcs, self.rcs)
    assert ccs == self.ccs, "Global detach/restore changed the registered constrained choices from %s to %s" % (ccs, self.ccs)
    assert aes == self.aes, "Global detach/restore changed the registered AEKernels from %s to %s" % (aes, self.aes)

    for scope_name in OrderedSet(scopes.keys()).union(self.scopes.keys()):
      if scope_name in scopes and scope_name not in self.scopes:
        assert False, "Global detach/restore destroyed scope %s with blocks %s" % (scope_name, scopes[scope_name])
      if scope_name not in scopes and scope_name in self.scopes:
        assert False, "Global detach/restore created scope %s with blocks %s" % (scope_name, self.scopes[scope_name])
      scope = scopes[scope_name]
      new_scope = self.scopes[scope_name]
      for block_name in OrderedSet(scope.keys()).union(new_scope.keys()):
        if block_name in scope and block_name not in new_scope:
          assert False, "Global detach/restore destroyed block %s, %s with nodes %s" % (scope_name, block_name, scope[block_name])
        if block_name not in scope and block_name in new_scope:
          assert False, "Global detach/restore created block %s, %s with nodes %s" % (scope_name, block_name, new_scope[block_name])
        assert scope[block_name] == new_scope[block_name], "Global detach/restore changed the addresses in block %s, %s from %s to %s" %(scope_name, block_name, scope[block_name], new_scope[block_name])

    assert_allclose(rhoWeight, xiWeight, err_msg="Global restore gave different weight from detach")
    # print "End invariant check"

  def get_current_values(self, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    from infer.mh import getCurrentValues
    currentValues = getCurrentValues(self, pnodes)
    for val in currentValues:
      assert val is not None, "Tried to get_current_values of a detached subproblem"
    return currentValues

  def block_values(self, scope, block):
    """Return a map between the addresses and values of principal nodes in
the scaffold determined by the given expression."""
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    scaffold = BlockScaffoldIndexer(scope, block).sampleIndex(self)
    return dict([(node.address, self.valueAt(node)) for node in scaffold.getPrincipalNodes()])

  def get_seed(self):
    # TODO Trace does not support seed control because it uses
    # Python's native randomness.
    return 0

  #### Serialization interface

  def makeSerializationDB(self, values=None, skipStackDictConversion=False):
    if values is not None:
      if not skipStackDictConversion:
        values = map(self.unboxValue, values)
    return OrderedOmegaDB(self, values)

  def dumpSerializationDB(self, db, skipStackDictConversion=False):
    values = db.listValues()
    if not skipStackDictConversion:
      values = map(self.boxValue, values)
    return values

  def unevalAndExtract(self, id, db):
    # leaves trace in an inconsistent state. use restore afterward
    assert id in self.families
    unevalFamily(self, self.families[id], Scaffold(), db)

  def restore(self, id, db):
    assert id in self.families
    restore(self, self.families[id], Scaffold(), db, OrderedDict())

  def evalAndRestore(self, id, exp, db):
    assert id not in self.families
    (_, self.families[id]) = evalFamily(
      self, Address(List(id)), self.unboxExpression(exp), self.globalEnv,
      Scaffold(), True, db, OrderedDict())

  def has_own_prng(self): return True
  def set_seed(self, seed):
    assert seed is not None
    prng = random.Random(seed)
    self.np_prng.seed(prng.random())
    self.py_prng.seed(prng.random())

  def short_circuit_copyable(self): return False

  #### Helpers (shouldn't be class methods)

  def boxValue(self, val): return val.asStackDict(self)
  @staticmethod
  def unboxValue(val): return VentureValue.fromStackDict(val)
  def unboxExpression(self, exp):
    return ExpressionType().asPython(VentureValue.fromStackDict(exp))

#################### Misc for particle commit

  def addNewMadeSPFamilies(self, node, newMadeSPFamilies):
    for id, root in newMadeSPFamilies.iteritems():
      node.madeSPRecord.spFamilies.registerFamily(id, root)

  def addNewChildren(self, node, newChildren):
    for child in newChildren:
      node.children.add(child)

  #### Configuration

  def set_profiling(self, enabled=True):
    self.profiling_enabled = enabled

  def clear_profiling(self):
    self.stats = []
