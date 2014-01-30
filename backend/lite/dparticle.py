import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

### TODO be careful about the boxing and unboxing
class Particle(trace.Trace):

  # The trace is expected to be a torus, with the chosen scaffold
  # already detached, or a particle.
  def __init__(self,trace):
    if type(trace) is Particle: initFromParticle(self,trace)
    elif type(trace) is Trace: initFromTrace(self,trace)
    else: raise Exception("Must init particle from trace or particle")

  # Note: using "copy()" informally for both legit_copy and persistent_copy
  def initFromParticle(self,particle):
    self.base = particle.base    

    # (1) Persistent Sets
    self.rcs = particle.rcs.pcopy()
    self.ccs = particle.ccs.pcopy()
    self.aes = particle.aes.pcopy()
    self.sbns = particle.sbns.pcopy()

    # (2) Persistent Maps to constants
    self.values = particle.values.pcopy()
    self.madeSPs = particle.madeSPs.pcopy()

    # (3) Persistent Maps to things that change through particle methods only
    self.esrParents = particle.esrParents.pcopy()
    self.scopesToBlocks = particle.scopesToBlocks.pcopy()
    self.numRequests = particle.numRequests.pcopy()
    self.regenCounts = particle.regenCounts.pcopy()
    self.madeSPFamilies = particle.madeSPFamilies.pcopy()
    self.newChildren = particle.newChildren.pcopy()
    # note: this is a legit map, but it shouldn't matter other than the copy cost which should be negligible
    self.scopesToBlocks = { scope : blocks.pcopy() for scope,blocks in particle.scopesToBlocks} # { scope => pset { block } }
    
    # (4) Maps to things that change outside of particle methods
    self.madeSPAuxs = { node => spaux.copy() for node,spaux in particle.madeSPAuxs }

  def initFromTrace(self,trace): raise Exception("Not yet implemented")

######################### (1) Persistent Sets
  def registerRandomChoice(self,node): 
    self.rcs.add(node)
    self.registerRandomChoiceInScope(self,"default",node,node)

  def registerAEKernel(self,node): self.aes.add(node)

  def registerConstrainedChoice(self,node): 
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def registerRandomChoiceInScope(self,scope,block,node): 
    self.sbns.add((scope,block,node))
    self._registerBlockInScope(scope,block)

######################### (2) Persistent Maps to constants

#### Getters
  
  def valueAt(self,node): 
    if node in self.values: return self.values[node]
    else: return self.base.valueAt(node)

  def madeSPAt(self,node):
    if node in self.madeSPs: return self.madeSPs[node]
    else: return self.base.madeSPAt(node)

#### Setters

  def setValueAt(self,node,value): 
    assert self.base.valueAt(node) is None
    self.values[node] = value

  def setMadeSPAt(self,node,sp): 
    assert not node in self.madeSPs
    assert self.base.madeSPAt(node) is None
    self.madeSPs[node] = sp


######################## (3) Persistent Maps to things that change through particle methods only

#### Getters (do not need to cache on reads)
  def esrParentsAt(self,node): 
    if node in self.esrParents: return self.esrParents[node]
    else: return self.base.esrParentsAt(node)

  def regenCountAt(self,scaffold,node): 
    if node in self.regenCounts: return self.regenCounts[node]
    else: return self.base.regenCountAt(scaffold,node)

  def containsSPFamilyAt(self,node,id): 
    if node in self.madeSPFamilies and id in self.madeSPFamilies[node]: return True
    else: return self.base.containsSPFamilyAt(node,id)

#### Setters (need to cache on writes)
  def appendEsrParentAt(self,node,parent):
    assert not self.base.esrParentsAt(node)
    if not node in self.esrParents: self.esrParents[node] = []
    self.esrParents[node].append(parent)

  def incRequestsAt(self,node):
    if not node in self.numRequests: self.numRequests[node] = self.base.numRequests[node]
    self.numRequests[node] += 1

  def addChildAt(self,node,child):
    if not node in self.newChildren: self.newChildren[node] = []
    self.newChildren[node].append(child)

  def incRegenCountAt(self,scaffold,node): 
    if not node in self.regenCounts: self.regenCounts[node] = 0
    self.regenCounts[node] += 1

  # initialization only
  def setMadeSPFamiliesAt(self,node,madeSPFamilies):
    assert not node in self.madeSPFamilies
    assert node.madeSPFamilies is None
    self.madeSPFamilies[node] = madeSPFamilies

  # TODO SUBTLE! Regular in trace, persistent for particles
  def registerFamilyAt(self,node,esrId,esrParent): 
    makerNode = node.spRef().makerNode
    if not makerNode in self.madeSPFamilies: self.madeSPFamilies[makerNode] = pmap()
    self.madeSPFamilies[makerNode][esrId] = esrParent

  # NOTE this map is not persistent, but the same semantics applies (and it maps to a persistent set)
  def _registerBlockInScope(self,scope,block):
    if not scope in self.scopesToBlocks: self.scopesToBlocks[scope] = pset()
    scopesToBlocks[scope].add(block)

######################## (4) Persistent Maps to things that change outside of particle methods

#### Getters (need to cache on reads)

  def madeSPAuxAt(self,node):
    if not node in self.madeSPAuxs: self.madeSPAuxs[node] = self.base.madeSPAuxAt(node).copy()
    return self.madeSPAuxs[node]

#### Setters (initializers only)

  def setMadeSPAuxAt(self,node,aux):
    assert not node in self.madeSPAuxs
    assert self.base.madeSPAuxAt(node) is None
    self.madeSPAuxs[node] = aux

######################## Miscellaneous bookkeeping
  # TODO subtle: 
  # How should we handle this bookkeeping?
  def numBlocksInScope(self,scope): raise Exception("Not yet implemented")

  # TODO
  def commit(self): raise Exception("Not yet implemented")

################### Methods that should never be called on particles
  def unregisterFamilyAt(self,node,esrId): raise Exception("Should not be called on a particle")
  def madeSPFamiliesAt(self,node): raise Exception("Should not be called on a particle")
  def popEsrParentAt(self,node): raise Exception("Should not be called on a particle")
  def childrenAt(self,node): raise Exception("Should not be called on a particle")
  def removeChildAt(self,node,child): raise Exception("Should not be called on a particle")
  def decRequestsAt(self,node): raise Exception("Should not be called on a particle")
  def unregisterAEKernel(self,node): raise Exception("Should not be called on a particle")
  def unregisterRandomChoice(self,node): raise Exception("Should not be called on a particle")
  def unregisterRandomChoiceInScope(self,scope,block,node): raise Exception("Should not be called on a particle")
  def unregisterConstrainedChoice(self,node): raise Exception("Should not be called on a particle")
  def decRegenCountAt(self,scaffold,node): raise Exception("Should never be called on a particle")
  def numRequestsAt(self,node): raise Exception("Should not be called on a particle")

################## Pipeline
  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def unregisterRandomChoiceInScope(self,scope,block,node):
    self.sbns.remove((scope,block,node))
    self._unregisterBlockInScope(scope,block)

  def _unregisterBlockInScope(self,scope,block):
    self.scopeToBlocks[scope].remove(block)
  def _registerBlockInScope(self,scope,block):
    if not scope in self.scopesToBlocks: self.scopesToBlocks[scope] = pset()
    scopesToBlocks[scope].add(block)
