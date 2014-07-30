from builtin import builtInValues, builtInSPs
from env import VentureEnvironment
from node import Node,ConstantNode,LookupNode,RequestNode,OutputNode,Args
import math
from regen import constrain, processMadeSP, evalFamily, restore
from detach import unconstrain, unevalFamily
from value import SPRef, ExpressionType, VentureValue, VentureSymbol
from scaffold import Scaffold
from infer import (mixMH,MHOperator,MeanfieldOperator,BlockScaffoldIndexer,
                   EnumerativeGibbsOperator,PGibbsOperator,ParticlePGibbsOperator,
                   RejectionOperator, MissingEsrParentError, NoSPRefError,
                   HamiltonianMonteCarloOperator, MAPOperator, StepOutSliceOperator,
                   DoublingSliceOperator, NesterovAcceleratedGradientAscentOperator)
from omegadb import OmegaDB
from smap import SMap
from sp import SPFamilies, VentureSPRecord
from scope import isScopeIncludeOutputPSP, isScopeExcludeOutputPSP
from regen import regenAndAttach
from detach import detachAndExtract
from scaffold import constructScaffold
from consistency import assertTorus
from lkernel import DeterministicLKernel
from psp import ESRRefOutputPSP
from serialize import OrderedOmegaDB
import random
import numpy.random

class Trace(object):
  def __init__(self):

    self.globalEnv = VentureEnvironment()
    for name,val in builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name,sp in builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.globalEnv = VentureEnvironment(self.globalEnv) # New frame so users can shadow globals

    self.rcs = set()
    self.ccs = set()
    self.aes = set()
    self.unpropagatedObservations = {} # {node:val}
    self.families = {}
    self.scopes = {} # :: {scope-name:smap{block-id:set(node)}}

    self.stats = {} # :: {name:[(time taken, was accepted?)]}

  def scope_keys(self):
    # A hack for allowing scope names not to be quoted in inference
    # programs (needs to be a method so Puma can implement it)
    return self.scopes.keys()

  def bindPrimitiveName(self, name, val):
    self.globalEnv.addBinding(name,ConstantNode(val))

  def bindPrimitiveSP(self, name, sp):
    spNode = self.createConstantNode(VentureSPRecord(sp))
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
    if not scope in self.scopes: self.scopes[scope] = SMap()
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
    assert not scope == "default" or len(self.scopes[scope][block]) == 0
    if len(self.scopes[scope][block]) == 0: del self.scopes[scope][block]
    if len(self.scopes[scope]) == 0: del self.scopes[scope]

  # [FIXME] repetitive, but not sure why these exist at all
  def _normalizeEvaluatedScope(self, scope):
    if scope == "default": return scope
    else:
      assert isinstance(scope, VentureValue)
      if isinstance(scope, VentureSymbol): return scope.getSymbol()
      else: return scope.getNumber()

  def _normalizeEvaluatedScopeAndBlock(self, scope, block):
    if scope == "default":
      assert isinstance(block, Node)
      return (scope, block)
    else:
      assert isinstance(scope, VentureValue)
      assert isinstance(block, VentureValue)
      # TODO probably want to allow arbitrary values as scopes and
      # blocks; but this requires converting them from the inference
      # program.
      if isinstance(scope, VentureSymbol):
        return (scope.getSymbol(), block.getNumber())
      else:
        return (scope.getNumber(), block.getNumber())

  def registerConstrainedChoice(self,node):
    assert node not in self.ccs, "Cannot constrain the same random choice twice."
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def unregisterConstrainedChoice(self,node):
    assert node in self.ccs
    self.ccs.remove(node)
    if self.pspAt(node).isRandom(): self.registerRandomChoice(node)

  def createConstantNode(self,val): return ConstantNode(val)
  def createLookupNode(self,sourceNode):
    lookupNode = LookupNode(sourceNode)
    self.setValueAt(lookupNode,self.valueAt(sourceNode))
    self.addChildAt(sourceNode,lookupNode)
    return lookupNode

  def createApplicationNodes(self,operatorNode,operandNodes,env):
    requestNode = RequestNode(operatorNode,operandNodes,env)
    outputNode = OutputNode(operatorNode,operandNodes,requestNode,env)
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
      raise NoSPRefError("spRef not an spRef but a %s at node %s with operator %s" % (type(candidate), node, node.operatorNode))
    assert isinstance(candidate, SPRef)
    return candidate

  def spAt(self,node): return self.madeSPAt(self.spRefAt(node).makerNode)
  def spFamiliesAt(self,node):
    spFamilies = self.madeSPFamiliesAt(self.spRefAt(node).makerNode)
    assert isinstance(spFamilies,SPFamilies)
    return spFamilies
  def spauxAt(self,node): return self.madeSPAuxAt(self.spRefAt(node).makerNode)
  def pspAt(self,node):
    if isinstance(node, RequestNode):
      return self.spAt(node).requestPSP
    else:
      assert isinstance(node, OutputNode)
      return self.spAt(node).outputPSP

  #### Stuff that a particle trace would need to override for persistence

  def valueAt(self,node):
    assert node.isAppropriateValue(node.value)
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
    assert node.aaaMadeSPAux is not None
    node.aaaMadeSPAux = None
  def registerAAAMadeSPAuxAt(self,node,aux):
    assert node.aaaMadeSPAux is None
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
  def sampleBlock(self,scope): return self.scopes[scope].sample()[0]
  def logDensityOfBlock(self,scope): return -1 * math.log(self.numBlocksInScope(scope))
  def blocksInScope(self,scope): return self.scopes[scope].keys()
  def numBlocksInScope(self,scope):
    if scope in self.scopes: return len(self.scopes[scope].keys())
    else: return 0

  def getAllNodesInScope(self,scope):
    return set.union(*[self.getNodesInBlock(scope,block) for block in self.scopes[scope].keys()])

  def getOrderedSetsInScope(self,scope,interval=None):
    if interval is None:
      return [self.getNodesInBlock(scope,block) for block in sorted(self.scopes[scope].keys())]
    else:
      blocks = [b for b in self.scopes[scope].keys() if b >= interval[0] if b <= interval[1]]
      return [self.getNodesInBlock(scope,block) for block in sorted(blocks)]

  def numNodesInBlock(self,scope,block): return len(self.getNodesInBlock(scope,block))

  def getNodesInBlock(self,scope,block):
    nodes = self.scopes[scope][block]
    if scope == "default": return nodes
    else:
      pnodes = set()
      for node in nodes: self.addRandomChoicesInBlock(scope,block,pnodes,node)
      return pnodes

  def addRandomChoicesInBlock(self,scope,block,pnodes,node):
    if not isinstance(node,OutputNode): return

    if self.pspAt(node).isRandom() and not node in self.ccs: pnodes.add(node)

    requestNode = node.requestNode
    if self.pspAt(requestNode).isRandom() and not requestNode in self.ccs: pnodes.add(requestNode)

    for esr in self.valueAt(node.requestNode).esrs:
      self.addRandomChoicesInBlock(scope,block,pnodes,self.spFamilyAt(requestNode,esr.id))

    self.addRandomChoicesInBlock(scope,block,pnodes,node.operatorNode)

    for i,operandNode in enumerate(node.operandNodes):
      if i == 2 and isScopeIncludeOutputPSP(self.pspAt(node)):
        (new_scope,new_block,_) = [self.valueAt(randNode) for randNode in node.operandNodes]
        (new_scope,new_block) = self._normalizeEvaluatedScopeAndBlock(new_scope, new_block)
        if scope != new_scope or block == new_block: self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)
      elif i == 1 and isScopeExcludeOutputPSP(self.pspAt(node)):
        (excluded_scope,_) = [self.valueAt(randNode) for randNode in node.operandNodes]
        excluded_scope = self._normalizeEvaluatedScope(excluded_scope)
        if scope != excluded_scope: self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)
      else:
        self.addRandomChoicesInBlock(scope,block,pnodes,operandNode)


  def scopeHasEntropy(self,scope):
    # right now scope in self.scopes iff it has entropy
    return scope in self.scopes and self.numBlocksInScope(scope) > 0

  def recordProposal(self, name, time, accepted):
    name = str(name)
    if name not in self.stats:
      self.stats[name] = []
    self.stats[name].append((time, accepted))

  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,self.unboxExpression(exp),self.globalEnv,Scaffold(),False,OmegaDB(),{})

  def bindInGlobalEnv(self,sym,id): self.globalEnv.addBinding(sym,self.families[id])
  def unbindInGlobalEnv(self,sym): self.globalEnv.removeBinding(sym)

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
      if xiWeight == float("-inf"): raise Exception("Unable to propagate constraint")
      node.observe(val)
      constrain(self,appNode,node.observedValue)
      weight += xiWeight
      weight -= rhoWeight
    self.unpropagatedObservations.clear()
    return weight

  def getConstrainableNode(self, node):
    candidate = self.getOutermostNonReferenceNode(node)
    if isinstance(candidate,ConstantNode): raise Exception("Cannot constrain a constant value.")
    if not self.pspAt(candidate).isRandom():
      raise Exception("Cannot constrain a deterministic value.")
    return candidate

  def getOutermostNonReferenceNode(self,node):
    if isinstance(node,ConstantNode): return node
    if isinstance(node,LookupNode): return self.getOutermostNonReferenceNode(node.sourceNode)
    assert isinstance(node,OutputNode)
    if isinstance(self.pspAt(node),ESRRefOutputPSP):
      if self.esrParentsAt(node):
        return self.getOutermostNonReferenceNode(self.esrParentsAt(node)[0])
      else:
        # Could happen if this method is called on a torus, e.g. for rejection sampling
        raise MissingEsrParentError()
    elif isScopeIncludeOutputPSP(self.pspAt(node)):
      return self.getOutermostNonReferenceNode(node.operandNodes[2])
    else: return node

  def unobserve(self,id):
    node = self.families[id]
    appNode = self.getConstrainableNode(node)
    if node.isObservation:
      unconstrain(self,appNode)
      node.isObservation = False
    else:
      assert node in self.unpropagatedObservations
      del self.unpropagatedObservations[node]

  def uneval(self,id):
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(),OmegaDB())
    del self.families[id]

  def numRandomChoices(self):
    return len(self.rcs)

  def infer_exp(self,exp):
    assert len(exp) >= 4
    (operator, scope, block) = exp[0:3]
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
        mixMH(self, BlockScaffoldIndexer(scope, block), MHOperator())
      elif operator == "meanfield":
        steps = int(exp[3])
        mixMH(self, BlockScaffoldIndexer(scope, block), MeanfieldOperator(steps, 0.0001))
      elif operator == "hmc":
        (epsilon,  L) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), HamiltonianMonteCarloOperator(epsilon, int(L)))
      elif operator == "gibbs":
        mixMH(self, BlockScaffoldIndexer(scope, block), EnumerativeGibbsOperator())
      elif operator == "slice":
        (w, m) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), StepOutSliceOperator(w, m))
      elif operator == "slice_doubling":
        (w, p) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), DoublingSliceOperator(w, p))
      elif operator == "pgibbs":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block)), PGibbsOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block), PGibbsOperator(particles))
      elif operator == "func_pgibbs":
        particles = int(exp[3])
        if isinstance(block, list): # Ordered range
          (_, min_block, max_block) = block
          mixMH(self, BlockScaffoldIndexer(scope, "ordered_range", (min_block, max_block)), ParticlePGibbsOperator(particles))
        else:
          mixMH(self, BlockScaffoldIndexer(scope, block), ParticlePGibbsOperator(particles))
      elif operator == "map":
        (rate, steps) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), MAPOperator(rate, int(steps)))
      elif operator == "nesterov":
        (rate, steps) = exp[3:5]
        mixMH(self, BlockScaffoldIndexer(scope, block), NesterovAcceleratedGradientAscentOperator(rate, int(steps)))
      elif operator == "rejection":
        mixMH(self, BlockScaffoldIndexer(scope, block), RejectionOperator())
      else: raise Exception("INFER %s is not implemented" % operator)

      for node in self.aes: self.madeSPAt(node).AEInfer(self.madeSPAuxAt(node))

  def get_seed(self):
    # TODO Trace does not support seed control because it uses
    # Python's native randomness.
    return 0

  def set_seed(self, seed):
    # random.seed(seed)
    # numpy.random.seed(seed)
    pass

  def getDirectiveLogScore(self,id):
    assert id in self.families
    node = self.getOutermostNonReferenceNode(self.families[id])
    return self.pspAt(node).logDensity(self.groundValueAt(node),self.argsAt(node))

  def getGlobalLogScore(self):
    return sum([self.pspAt(node).logDensity(self.groundValueAt(node),self.argsAt(node)) for node in self.rcs.union(self.ccs)])

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
    (_,self.families[id]) = evalFamily(self,self.unboxExpression(exp),self.globalEnv,Scaffold(),True,db,{})

  #### Helpers (shouldn't be class methods)

  # TODO temporary, probably need an extra layer of boxing for VentureValues
  # as in CXX
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




