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

import math

from venture.exception import VentureException
from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.builtin import builtInSPs
from venture.lite.builtin import builtInValues
from venture.lite.detach import detachAndExtract
from venture.lite.detach import unconstrain
from venture.lite.detach import unevalFamily
from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.exception import VentureError
from venture.lite.infer import BlockScaffoldIndexer
from venture.lite.infer import mixMH
from venture.lite.lkernel import DeterministicLKernel
from venture.lite.node import Args
from venture.lite.node import ConstantNode
from venture.lite.node import LookupNode
from venture.lite.node import OutputNode
from venture.lite.node import RequestNode
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.omegadb import OmegaDB
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
from venture.lite.value import VentureNumber
from venture.lite.value import VenturePair
from venture.lite.value import VentureSymbol
from venture.lite.value import VentureValue
import venture.lite.infer as infer

class Trace(object):
  def __init__(self):

    self.globalEnv = VentureEnvironment()
    for name,val in builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name,sp in builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

    self.rcs = set()
    self.ccs = set()
    self.aes = set()
    self.unpropagatedObservations = {} # {node:val}
    self.families = {}
    self.scopes = {} # :: {scope-name:smap{block-id:set(node)}}

    self.profiling_enabled = False
    self.stats = []

  def scope_keys(self):
    # A hack for allowing scope names not to be quoted in inference
    # programs (needs to be a method so Puma can implement it)
    return self.scopes.keys()

  def sealEnvironment(self):
    self.globalEnv = VentureEnvironment(self.globalEnv)

  def bindPrimitiveName(self, name, val):
    self.globalEnv.addBinding(name,self.createConstantNode(None, val))

  def bindPrimitiveSP(self, name, sp):
    spNode = self.createConstantNode(None, VentureSPRecord(sp))
    processMadeSP(self,spNode,False)
    assert isinstance(self.valueAt(spNode), SPRef)
    self.globalEnv.addBinding(name,spNode)

  def registerAEKernel(self,node): self.aes.add(node)
  def unregisterAEKernel(self,node): self.aes.remove(node)

  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.add(node)
    self.registerRandomChoiceInScope("default",node,node)

  def registerRandomChoiceInScope(self,scope,block,node,unboxed=False):
    if not unboxed: (scope, block) = self._normalizeEvaluatedScopeAndBlock(scope, block)
    if not scope in self.scopes: self.scopes[scope] = SamplableMap()
    if not block in self.scopes[scope]: self.scopes[scope][block] = set()
    assert not node in self.scopes[scope][block]
    self.scopes[scope][block].add(node)
    assert not scope == "default" or len(self.scopes[scope][block]) == 1

  def unregisterRandomChoice(self,node):
    assert node in self.rcs
    self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def unregisterRandomChoiceInScope(self,scope,block,node):
    (scope, block) = self._normalizeEvaluatedScopeAndBlock(scope, block)
    self.scopes[scope][block].remove(node)
    if scope == "default":
      assert len(self.scopes[scope][block]) == 0
    if len(self.scopes[scope][block]) == 0: del self.scopes[scope][block]
    if len(self.scopes[scope]) == 0 and (not scope == "default"): del self.scopes[scope]

  def _normalizeEvaluatedScopeOrBlock(self, val):
    if isinstance(val, VentureNumber):
      return val.getNumber()
    elif isinstance(val, VentureSymbol):
      return val.getSymbol()
    elif isinstance(val, VenturePair): # I hope this means it's an ordered range
      return ExpressionType().asPython(val)
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

  def registerConstrainedChoice(self,node):
    if node in self.ccs:
      raise VentureException("evaluation", "Cannot constrain the same random choice twice.", address = node.address)
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def unregisterConstrainedChoice(self,node):
    assert node in self.ccs
    self.ccs.remove(node)
    if self.pspAt(node).isRandom(): self.registerRandomChoice(node)

  def createConstantNode(self,address,val): return ConstantNode(address,val)
  def createLookupNode(self,address,sourceNode):
    lookupNode = LookupNode(address,sourceNode)
    self.setValueAt(lookupNode,self.valueAt(sourceNode))
    self.addChildAt(sourceNode,lookupNode)
    return lookupNode

  def createApplicationNodes(self,address,operatorNode,operandNodes,env):
    requestNode = RequestNode(address,operatorNode,operandNodes,env)
    outputNode = OutputNode(address,operatorNode,operandNodes,requestNode,env)
    self.addChildAt(operatorNode,requestNode)
    self.addChildAt(operatorNode,outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode,requestNode)
      self.addChildAt(operandNode,outputNode)
    requestNode.registerOutputNode(outputNode)
    return (requestNode,outputNode)

  def addESREdge(self,esrParent,outputNode):
    self.incRequestsAt(esrParent)
    self.addChildAt(esrParent,outputNode)
    self.appendEsrParentAt(outputNode,esrParent)

  def popLastESRParent(self,outputNode):
    assert self.esrParentsAt(outputNode)
    esrParent = self.popEsrParentAt(outputNode)
    self.removeChildAt(esrParent,outputNode)
    self.decRequestsAt(esrParent)
    return esrParent

  def disconnectLookup(self,lookupNode):
    self.removeChildAt(lookupNode.sourceNode,lookupNode)

  def reconnectLookup(self,lookupNode):
    self.addChildAt(lookupNode.sourceNode,lookupNode)

  def groundValueAt(self,node):
    value = self.valueAt(node)
    if isinstance(value,SPRef): return self.madeSPRecordAt(value.makerNode)
    else: return value

  def argsAt(self,node): return Args(self,node)

  def spRefAt(self,node):
    candidate = self.valueAt(node.operatorNode)
    if not isinstance(candidate, SPRef):
      raise infer.NoSPRefError("Cannot apply a non-procedure: %s (at node %s with operator %s)" % (candidate, node, node.operatorNode))
    assert isinstance(candidate, SPRef)
    return candidate

  def spAt(self,node): return self.madeSPAt(self.spRefAt(node).makerNode)
  def spFamiliesAt(self,node):
    spFamilies = self.madeSPFamiliesAt(self.spRefAt(node).makerNode)
    assert isinstance(spFamilies,SPFamilies)
    return spFamilies
  def spauxAt(self,node): return self.madeSPAuxAt(self.spRefAt(node).makerNode)
  def pspAt(self,node): return node.relevantPSP(self.spAt(node))

  #### Stuff that a particle trace would need to override for persistence

  def valueAt(self,node):
    return node.value

  def setValueAt(self,node,value):
    assert node.isAppropriateValue(value)
    node.value = value

  def madeSPRecordAt(self,node):
    assert node.madeSPRecord is not None
    return node.madeSPRecord

  def setMadeSPRecordAt(self,node,spRecord):
    node.madeSPRecord = spRecord

  def madeSPAt(self,node): return self.madeSPRecordAt(node).sp
  def setMadeSPAt(self,node,sp):
    spRecord = self.madeSPRecordAt(node)
    spRecord.sp = sp

  def madeSPFamiliesAt(self,node): return self.madeSPRecordAt(node).spFamilies
  def setMadeSPFamiliesAt(self,node,families):
    spRecord = self.madeSPRecordAt(node)
    spRecord.spFamilies = families

  def madeSPAuxAt(self,node): return self.madeSPRecordAt(node).spAux
  def setMadeSPAuxAt(self,node,aux):
    spRecord = self.madeSPRecordAt(node)
    spRecord.spAux = aux

  def getAAAMadeSPAuxAt(self,node): return node.aaaMadeSPAux
  def discardAAAMadeSPAuxAt(self,node):
    node.aaaMadeSPAux = None
  def registerAAAMadeSPAuxAt(self,node,aux):
    node.aaaMadeSPAux = aux

  def parentsAt(self,node): return node.parents()
  def definiteParentsAt(self,node): return node.definiteParents()

  def esrParentsAt(self,node): return node.esrParents
  def setEsrParentsAt(self,node,parents): node.esrParents = parents
  def appendEsrParentAt(self,node,parent): node.esrParents.append(parent)
  def popEsrParentAt(self,node): return node.esrParents.pop()

  def childrenAt(self,node): return node.children
  def setChildrenAt(self,node,children): node.children = children
  def addChildAt(self,node,child): node.children.add(child)
  def removeChildAt(self,node,child): node.children.remove(child)

  def registerFamilyAt(self,node,esrId,esrParent): self.spFamiliesAt(node).registerFamily(esrId,esrParent)
  def unregisterFamilyAt(self,node,esrId): self.spFamiliesAt(node).unregisterFamily(esrId)
  def containsSPFamilyAt(self,node,esrId): return self.spFamiliesAt(node).containsFamily(esrId)
  def spFamilyAt(self,node,esrId): return self.spFamiliesAt(node).getFamily(esrId)
  def madeSPFamilyAt(self,node,esrId): return self.madeSPFamiliesAt(node).getFamily(esrId)

  def initMadeSPFamiliesAt(self,node): self.setMadeSPFamiliesAt(node,SPFamilies())
  def clearMadeSPFamiliesAt(self,node): self.setMadeSPFamiliesAt(node,None)

  def numRequestsAt(self,node): return node.numRequests
  def setNumRequestsAt(self,node,num): node.numRequests = num
  def incRequestsAt(self,node): node.numRequests += 1
  def decRequestsAt(self,node): node.numRequests -= 1

  def regenCountAt(self,scaffold,node): return scaffold.regenCounts[node]
  def incRegenCountAt(self,scaffold,node): scaffold.regenCounts[node] += 1
  def decRegenCountAt(self,scaffold,node): scaffold.regenCounts[node] -= 1 # need not be overriden

  def isConstrainedAt(self,node): return node in self.ccs

  #### For kernels
  def getScope(self, scope): return self.scopes[self._normalizeEvaluatedScopeOrBlock(scope)]

  def sampleBlock(self,scope): return self.getScope(scope).sample()[0]
  def logDensityOfBlock(self,scope): return -1 * math.log(self.numBlocksInScope(scope))
  def blocksInScope(self,scope): return self.getScope(scope).keys()
  def numBlocksInScope(self,scope):
    scope = self._normalizeEvaluatedScopeOrBlock(scope)
    if scope in self.scopes: return len(self.getScope(scope).keys())
    else: return 0

  def getAllNodesInScope(self,scope):
    blocks = [self.getNodesInBlock(scope,block) for block in self.getScope(scope).keys()]
    if len(blocks) == 0: # Guido, WTF?
      return set()
    else:
      return set.union(*blocks)

  def getOrderedSetsInScope(self,scope,interval=None):
    if interval is None:
      return [self.getNodesInBlock(scope,block) for block in sorted(self.getScope(scope).keys())]
    else:
      blocks = [b for b in self.getScope(scope).keys() if b >= interval[0] if b <= interval[1]]
      return [self.getNodesInBlock(scope,block) for block in sorted(blocks)]

  def numNodesInBlock(self,scope,block): return len(self.getNodesInBlock(scope,block))

  def getNodesInBlock(self,scope,block):
    #import pdb; pdb.set_trace()
    #scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    nodes = self.scopes[scope][block]
    if scope == "default": return nodes
    else:
      pnodes = set()
      for node in nodes: self.addRandomChoicesInBlock(scope,block,pnodes,node)
      return pnodes

  def addRandomChoicesInBlock(self,scope,block,pnodes,node):
    if not isOutputNode(node): return

    if self.pspAt(node).isRandom() and not node in self.ccs: pnodes.add(node)

    requestNode = node.requestNode
    if self.pspAt(requestNode).isRandom() and not requestNode in self.ccs: pnodes.add(requestNode)

    for esr in self.valueAt(node.requestNode).esrs:
      self.addRandomChoicesInBlock(scope,block,pnodes,self.spFamilyAt(requestNode,esr.id))

    self.addRandomChoicesInBlock(scope,block,pnodes,node.operatorNode)

    for i,operandNode in enumerate(node.operandNodes):
      if i == 2 and isTagOutputPSP(self.pspAt(node)):
        (new_scope,new_block,_) = [self.valueAt(randNode) for randNode in node.operandNodes]
        (new_scope,new_block) = self._normalizeEvaluatedScopeAndBlock(new_scope, new_block)
        if scope != new_scope or block == new_block: self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)
      elif i == 1 and isTagExcludeOutputPSP(self.pspAt(node)):
        (excluded_scope,_) = [self.valueAt(randNode) for randNode in node.operandNodes]
        excluded_scope = self._normalizeEvaluatedScope(excluded_scope)
        if scope != excluded_scope: self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)
      else:
        self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)


  def scopeHasEntropy(self,scope):
    # right now scope in self.scopes iff it has entropy
    return self.numBlocksInScope(scope) > 0

  def recordProposal(self, **kwargs):
    if self.profiling_enabled:
      self.stats.append(kwargs)

  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,Address(List(id)),self.unboxExpression(exp),self.globalEnv,Scaffold(),False,OmegaDB(),{})

  def bindInGlobalEnv(self,sym,id):
    try:
      self.globalEnv.addBinding(sym,self.families[id])
    except VentureError as e:
      raise VentureException("invalid_argument", message=e.message, argument="symbol")

  def unbindInGlobalEnv(self,sym): self.globalEnv.removeBinding(sym)

  def boundInGlobalEnv(self, sym): return self.globalEnv.symbolBound(sym)

  def extractValue(self,id): return self.boxValue(self.valueAt(self.families[id]))

  def extractRaw(self,id): return self.valueAt(self.families[id])

  def observe(self,id,val):
    node = self.families[id]
    self.unpropagatedObservations[node] = self.unboxValue(val)

  def makeConsistent(self):
    weight = 0
    for node,val in self.unpropagatedObservations.iteritems():
      appNode = self.getConstrainableNode(node)
#      print "PROPAGATE",node,appNode
      scaffold = constructScaffold(self,[set([appNode])])
      rhoWeight,_ = detachAndExtract(self,scaffold)
      scaffold.lkernels[appNode] = DeterministicLKernel(self.pspAt(appNode),val)
      xiWeight = regenAndAttach(self,scaffold,False,OmegaDB(),{})
      # If xiWeight is -inf, we are in an impossible state, but that might be ok.
      # Finish constraining, to avoid downstream invariant violations.
      node.observe(val)
      constrain(self,appNode,node.observedValue)
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
    for node,val in self.unpropagatedObservations.iteritems():
      appNode = self.getConstrainableNode(node)
      #import ipdb; ipdb.set_trace()
      node.observe(val)
      constrain(self,appNode,node.observedValue)
    self.unpropagatedObservations.clear()

  def getConstrainableNode(self, node):
    candidate = self.getOutermostNonReferenceNode(node)
    if isConstantNode(candidate):
      raise VentureException("evaluation", "Cannot constrain a constant value.", address = node.address)
    if not self.pspAt(candidate).isRandom():
      raise VentureException("evaluation", "Cannot constrain a deterministic value.", address = node.address)
    return candidate

  def getOutermostNonReferenceNode(self,node):
    if isConstantNode(node): return node
    if isLookupNode(node): return self.getOutermostNonReferenceNode(node.sourceNode)
    assert isOutputNode(node)
    if isinstance(self.pspAt(node),ESRRefOutputPSP):
      if self.esrParentsAt(node):
        return self.getOutermostNonReferenceNode(self.esrParentsAt(node)[0])
      else:
        # Could happen if this method is called on a torus, e.g. for rejection sampling
        raise infer.MissingEsrParentError()
    elif isTagOutputPSP(self.pspAt(node)):
      return self.getOutermostNonReferenceNode(node.operandNodes[2])
    else: return node

  def unobserve(self,id):
    node = self.families[id]
    appNode = self.getConstrainableNode(node)
    if node.isObservation:
      weight = unconstrain(self,appNode)
      node.isObservation = False
    else:
      assert node in self.unpropagatedObservations
      del self.unpropagatedObservations[node]
      weight = 0
    return weight

  def uneval(self,id):
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(),OmegaDB())
    del self.families[id]

  def numRandomChoices(self):
    return len(self.rcs)

  def primitive_infer(self,exp):
    assert len(exp) >= 3
    (operator, scope, block) = exp[0:3]
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    if len(exp) == 3:
      transitions = 1
    else:
      maybe_transitions = exp[-1]
      if isinstance(maybe_transitions, bool):
        # The last item was the parallelism indicator
        transitions = int(exp[-2])
      else:
        transitions = int(exp[-1])
    if not self.scopeHasEntropy(scope):
      return
    for _ in range(transitions):
      if operator == "mh":
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.MHOperator())
      elif operator == "func_mh":
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.FuncMHOperator())
      elif operator == "draw_scaffold":
        infer.drawScaffold(self, BlockScaffoldIndexer(scope, block))
      elif operator == "mh_kernel_update":
        (useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:6]
        scaffolder = BlockScaffoldIndexer(scope, block,
          useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
          updateValues=updateValues)
        mixMH(self, scaffolder, infer.MHOperator())
      elif operator == "subsampled_mh":
        (Nbatch, k0, epsilon, useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:9]
        scaffolder = infer.SubsampledBlockScaffoldIndexer(scope, block,
          useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
          updateValues=updateValues)
        infer.subsampledMixMH(self, scaffolder, infer.SubsampledMHOperator(), Nbatch, k0, epsilon)
      elif operator == "subsampled_mh_check_applicability":
        infer.SubsampledBlockScaffoldIndexer(scope, block).checkApplicability(self)
      elif operator == "subsampled_mh_make_consistent":
        (useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:6]
        infer.SubsampledMHOperator().makeConsistent(self, infer.SubsampledBlockScaffoldIndexer(scope, block, useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs, updateValues=updateValues))
      elif operator == "meanfield":
        steps = int(exp[3])
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.MeanfieldOperator(steps, 0.0001))
      elif operator == "hmc":
        (epsilon,  L) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.HamiltonianMonteCarloOperator(epsilon, int(L)))
      elif operator == "gibbs":
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.EnumerativeGibbsOperator())
      elif operator == "emap":
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.EnumerativeMAPOperator())
      elif operator == "gibbs_update":
        mixMH(self, BlockScaffoldIndexer(scope, block, updateValues=True), infer.EnumerativeGibbsOperator())
      elif operator == "slice":
        (w, m) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.StepOutSliceOperator(w, m))
      elif operator == "slice_doubling":
        (w, p) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.DoublingSliceOperator(w, p))
      elif operator == "pgibbs":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block)), infer.PGibbsOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block), infer.PGibbsOperator(particles))
      elif operator == "pgibbs_update":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block), updateValues=True), infer.PGibbsOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block, updateValues=True), infer.PGibbsOperator(particles))
      elif operator == "func_pgibbs":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block)), infer.ParticlePGibbsOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block), infer.ParticlePGibbsOperator(particles))
      elif operator == "func_pmap":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block)), infer.ParticlePMAPOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block), infer.ParticlePMAPOperator(particles))
      elif operator == "grad_ascent":
        (rate, steps) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.GradientAscentOperator(rate, int(steps)))
      elif operator == "nesterov":
        (rate, steps) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.NesterovAcceleratedGradientAscentOperator(rate, int(steps)))
      elif operator == "rejection":
        if len(exp) == 5:
          trials = int(exp[3])
        else:
          trials = None
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.RejectionOperator(trials))
      elif operator == "bogo_possibilize":
        mixMH(self, BlockScaffoldIndexer(scope, block), infer.BogoPossibilizeOperator())
      elif operator == "print_scaffold_stats":
        BlockScaffoldIndexer(scope, block).sampleIndex(self).show()
      else: raise Exception("INFER %s is not implemented" % operator)

      for node in self.aes: self.madeSPAt(node).AEInfer(self.madeSPAuxAt(node))

  def log_likelihood_at(self, scope, block):
    # TODO This is a different control path from infer_exp because it
    # needs to return the weight
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    scaffold = BlockScaffoldIndexer(scope, block).sampleIndex(self)
    (_rhoWeight,rhoDB) = detachAndExtract(self, scaffold)
    xiWeight = regenAndAttach(self, scaffold, True, rhoDB, {})
    # Old state restored, don't need to do anything else
    return xiWeight

  def log_joint_at(self, scope, block):
    # TODO This is a different control path from infer_exp because it
    # needs to return the weight
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    scaffold = BlockScaffoldIndexer(scope, block).sampleIndex(self)
    pnodes = scaffold.getPrincipalNodes()
    from infer.mh import getCurrentValues, registerDeterministicLKernels
    currentValues = getCurrentValues(self, pnodes)
    registerDeterministicLKernels(self, scaffold, pnodes, currentValues)
    (_rhoWeight,rhoDB) = detachAndExtract(self, scaffold)
    xiWeight = regenAndAttach(self, scaffold, True, rhoDB, {})
    # Old state restored, don't need to do anything else
    return xiWeight

  def likelihood_weight(self):
    # TODO This is a different control path from infer_exp because it
    # needs to return the new weight
    scaffold = BlockScaffoldIndexer("default", "all").sampleIndex(self)
    (_rhoWeight,rhoDB) = detachAndExtract(self, scaffold)
    xiWeight = regenAndAttach(self, scaffold, False, rhoDB, {})
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
      unevalFamily(self,node,Scaffold(),OmegaDB())
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
    if operator == "enumerative":
      return infer.EnumerativeDiversify(copy_trace)(self, BlockScaffoldIndexer(scope, block))
    else: raise Exception("DIVERSIFY %s is not implemented" % operator)

  def select(self, scope, block):
    scope, block = self._normalizeEvaluatedScopeAndBlock(scope, block)
    assert not block == "one", "Accounting for stochastic subproblem selection not supported"
    scaffold = BlockScaffoldIndexer(scope, block).sampleIndex(self)
    return scaffold

  def just_detach(self, scaffold):
    return detachAndExtract(self, scaffold)

  def just_regen(self, scaffold):
    return regenAndAttach(self, scaffold, False, OmegaDB(), {})

  def just_restore(self, scaffold, rhoDB):
    return regenAndAttach(self, scaffold, True, rhoDB, {})

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
    xiWeight = regenAndAttach(self, scaffold, False, OmegaDB(), {})
    unregisterDeterministicLKernels(self, scaffold, pnodes) # de-mutate the scaffold in case it is used for subsequent operations
    return xiWeight

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

  def set_seed(self, seed):
    # random.seed(seed)
    # numpy.random.seed(seed)
    pass

  def getGlobalLogScore(self):
    # TODO This algorithm is totally wrong: https://app.asana.com/0/16653194948424/20100308871203
    all_scores = [self._getOneLogScore(node) for node in self.rcs.union(self.ccs)]
    scores, isLikelihoodFree = zip(*all_scores) if all_scores else [(), ()]
    return sum(scores)

  def _getOneLogScore(self, node):
    # Hack: likelihood-free PSP's contribute 0 to global logscore.
    # This is incorrect, but better than the function breaking entirely.
    try:
      return (self.pspAt(node).logDensity(self.groundValueAt(node),self.argsAt(node)), False)
    except VentureBuiltinSPMethodError:
      return (0.0, True)

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

  def unevalAndExtract(self,id,db):
    # leaves trace in an inconsistent state. use restore afterward
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(),db)

  def restore(self,id,db):
    assert id in self.families
    restore(self,self.families[id],Scaffold(),db,{})

  def evalAndRestore(self,id,exp,db):
    assert id not in self.families
    (_,self.families[id]) = evalFamily(self,Address(List(id)),self.unboxExpression(exp),self.globalEnv,Scaffold(),True,db,{})

  def has_own_prng(self): return False

  def short_circuit_copyable(self): return False

  #### Helpers (shouldn't be class methods)

  def boxValue(self,val): return val.asStackDict(self)
  @staticmethod
  def unboxValue(val): return VentureValue.fromStackDict(val)
  def unboxExpression(self,exp):
    return ExpressionType().asPython(VentureValue.fromStackDict(exp))

#################### Misc for particle commit

  def addNewMadeSPFamilies(self,node,newMadeSPFamilies):
    for id,root in newMadeSPFamilies.iteritems():
      node.madeSPRecord.spFamilies.registerFamily(id,root)

  def addNewChildren(self,node,newChildren):
    for child in newChildren:
      node.children.add(child)

  #### Configuration

  def set_profiling(self, enabled=True):
    self.profiling_enabled = enabled

  def clear_profiling(self):
    self.stats = []
