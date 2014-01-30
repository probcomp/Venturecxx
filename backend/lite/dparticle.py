import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

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

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = { node => spaux.copy() for node,spaux in particle.madeSPAuxs }

  def initFromTrace(self,trace):
    self.base = trace

    # (1) Persistent stuff
    self.rcs = PSet()
    self.ccs = PSet()
    self.aes = PSet()

    self.values = PMap()
    self.madeSPs = PMap()

    self.scopes = PMap()
    self.esrParents = PMap()
    self.numRequests = PMap()
    self.regenCounts = PMap()
    self.newMadeSPFamilies = PMap()
    self.newChildren = PMap()

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = {}


#### Random choices and scopes

  def registerRandomChoice(self,node):
    self.rcs = self.rcs.insert(node)
    self.registerRandomChoiceInScope(self,"default",node,node)

  def registerAEKernel(self,node): 
    self.aes = self.aes.insert(node)

  def registerConstrainedChoice(self,node): 
    self.ccs = self.ccs.insert(node)
    self.unregisterRandomChoice(node)

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    self.rcs = self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def registerRandomChoiceInScope(self,scope,block,node): 
    if not scope in self.scopes: self.scopes = self.scopes.insert(scope,PMap())
    if not block in self.scopes.lookup(scope): self.scopes.alter(scope,lambda blocks: blocks.insert(block,PSet()))
    self.scopes = self.scopes.alter(scope,lambda blocks: blocks.alter(block,lambda pnodes: pnodes.insert(node)))

  def unregisterRandomChoiceInScope(self,scope,block,node):
    self.scopes = self.scopes.alter(scope,lambda blocks: blocks.alter(block,lambda pnodes: pnodes.remove(node)))
    if self.scopes.lookup(scope).lookup(block).isEmpty(): self.scopes = self.scopes.alter(scope,lambda blocks: blocks.remove(block))
    if self.scopes.lookup(scope).isEmpty(): self.scopes = self.scopes.remove(scope)

#### Misc

  def valueAt(self,node): 
    if node in self.values: return self.values.lookup(node)
    else: return self.base.valueAt(node)

  def setValueAt(self,node,value): 
    assert self.base.valueAt(node) is None
    self.values = self.values.insert(node,value)

  def madeSPAt(self,node):
    if node in self.madeSPs: return self.madeSPs.lookup(node)
    else: return self.base.madeSPAt(node)

  def setMadeSPAt(self,node,sp): 
    assert not node in self.madeSPs
    assert self.base.madeSPAt(node) is None
    self.madeSPs = self.madeSPs.insert(node,sp)

  def esrParentsAt(self,node): 
    if node in self.esrParents: return self.esrParents.lookup(node)
    else: return self.base.esrParentsAt(node)

  def appendEsrParentAt(self,node,parent):
    assert not self.base.esrParentsAt(node)
    if not node in self.esrParents: self.esrParents = self.esrParents.insert(node,[])
    self.esrParents.lookup(node).append(parent)

  def regenCountAt(self,scaffold,node): 
    if node in self.regenCounts: return self.regenCounts.lookup(node)
    else: return self.base.regenCountAt(scaffold,node)

  def incRegenCountAt(self,scaffold,node): 
    if not node in self.regenCounts: self.regenCounts.insert(node,0)
    self.regenCounts.alter(node,lambda rc: rc + 1)

  def incRequestsAt(self,node):
    if not node in self.numRequests: self.numRequests = self.numRequests.insert(node,self.base.numRequests[node])
    self.numRequests.alter(node,lambda nr: nr + 1)

  def addChildAt(self,node,child):
    if not node in self.newChildren: self.newChildren.insert(node,[])
    self.newChildren.lookup(node).append(child)

### SPFamilies

  def containsSPFamilyAt(self,node,id): 
    if node in self.newMadeSPFamilies and id in self.newMadeSPFamilies.lookup(node): return True
    else: return self.base.containsSPFamilyAt(node,id)

  def setMadeSPFamiliesAt(self,node,madeSPFamilies):
    assert not node in self.newMadeSPFamilies
    assert node.madeSPFamilies is None
    self.newMadeSPFamilies = self.newMadeSPFamilies.insert(node,madeSPFamilies)

  def registerFamilyAt(self,node,esrId,esrParent): 
    makerNode = self.spRef(node).makerNode
    if not makerNode in self.newMadeSPFamilies: self.newMadeSPFamilies = self.newMadeSPFamilies.insert(makerNode,PMap())
    self.newMadeSPFamilies.alter(makerNode,lambda ids: ids.insert(esrId,esrParent))

### Regular maps

  def madeSPAuxAt(self,node):
    if not node in self.madeSPAuxs: self.madeSPAuxs[node] = self.base.madeSPAuxAt(node).copy()
    return self.madeSPAuxs[node]

  def setMadeSPAuxAt(self,node,aux):
    assert not node in self.madeSPAuxs
    assert self.base.madeSPAuxAt(node) is None
    self.madeSPAuxs[node] = aux

### Miscellaneous bookkeeping
  def numBlocksInScope(self,scope): return len(self.scopes.lookup(block)) + len(self.base.numBlocksInScope(scope))

### Commit
  def commit(self): 
    # note that we do not call registerRandomChoice() because it in turn calls registerRandomChoiceInScope()
    for node in self.rcs: self.base.rcs.add(node)

    # note that we do not call registerConstrainedChoice() because it in turn calls unregisterRandomChoice()
    for node in self.ccs: self.base.ccs.add(node)

    for node in self.aes: self.base.registerAEKernel(node)

    for (node,value) in self.values: self.base.setValueAt(node,value)
    for (node,madeSP) in self.madeSPs: self.base.setMadeSPAt(node,madeSP)

    # this iteration includes "default"
    for (scope,blocks) in self.scopes:
      for (block,pnodes) in blocks:
        for pnode in pnodes:
          self.base.registerRandomChoiceInScope(scope,block,pnode)
          
    for (node,esrParents) in self.esrParents: trace.setEsrParentsAt(node,esrParents)
    for (node,numRequests) in self.numRequests: trace.setNumRequestsAt(node,numRequests)
    for (node,newMadeSPFamilies) in self.newMadeSPFamilies: trace.addNewMadeSPFamilies(node,newMadeSPFamilies)
    for (node,newChildren) in self.newChildren: trace.addNewChildren(node,newChildren)

    for (node,spaux) in self.madeSPAuxs: trace.setMadeSPAuxAt(node,spaux)

################### Methods that should never be called on particles
  def unregisterFamilyAt(self,node,esrId): raise Exception("Should not be called on a particle")
  def madeSPFamiliesAt(self,node): raise Exception("Should not be called on a particle")
  def popEsrParentAt(self,node): raise Exception("Should not be called on a particle")
  def childrenAt(self,node): raise Exception("Should not be called on a particle")
  def removeChildAt(self,node,child): raise Exception("Should not be called on a particle")
  def decRequestsAt(self,node): raise Exception("Should not be called on a particle")
  def unregisterAEKernel(self,node): raise Exception("Should not be called on a particle")
  def unregisterConstrainedChoice(self,node): raise Exception("Should not be called on a particle")
  def decRegenCountAt(self,scaffold,node): raise Exception("Should never be called on a particle")
  def numRequestsAt(self,node): raise Exception("Should not be called on a particle")

