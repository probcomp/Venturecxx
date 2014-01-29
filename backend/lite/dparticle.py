import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

class Particle(trace.Trace):
  class PSets(object):
    def __init__(self,rcs,ccs,aes,sbns):
      # TODO
      # we don't have deletion yet, so we don't remove from rcs from a node that is ccs.
      # when we commit, we only commit the rcs that are not in ccs
      self.rcs = rcs
      self.ccs = ccs
      self.aes = aes
      self.sbns = sbns

  class PMaps(object):
    def __init__(self,values,madeSPs,esrParents,scopesToBlocks):
      self.values = values
      self.madeSPs = madeSPs
      self.esrParents = esrParents
      self.scopesToBlocks = scopesToBlocks

  class MapsToConstants(object):
    def __init__(self,numRequests,regenCounts):
      self.numRequests = numRequests
      self.regenCounts = regenCounts

  class MapsToPSets(object):
    def __init__(self,madeSPFamilies,newChildren):
      self.madeSPFamilies = madeSPFamilies
      self.newChildren = newChildren

  class MapsToUniqueClones(object):
    def __init__(self,madeSPAuxs):
      self.madeSPAuxs

  # The trace is expected to be a torus, with the chosen scaffold
  # already detached.
  def __init__(self,trace):
    if type(trace) is Particle: initFromParticle(self,trace)
    elif type(trace) is Trace: initFromTrace(self,trace)
    else: raise Exception("Must init particle from trace or particle")

  # Note: using "copy()" informally for both legit_copy and persistent_copy
  def initFromParticle(self,particle):
    self.base = particle.base    

    self.psets = self.PSets(particle.psets.rcs,
                            particle.psets.ccs,
                            particle.psets.aes,
                            particle.psets.sbns)

    self.pmaps = self.PMaps(particle.pmaps.values,
                            particle.pmaps.madeSPs,
                            particle.pmaps.esrParents,
                            particle.pmaps.scopesToBlocks)

    self.maps_to_constants = self.MapsToConstants(particle.numRequests.copy(),regenCounts.copy())
    self.maps_to_psets = self.MapsToPSets(particle.madeSPFamilies.copy(),particle.newChildren.copy())
    self.maps_to_clones = self.MapsToUniqueClones({ node => spaux.copy() for node,spaux in particle.madeSPAuxs })

  def initFromTrace(self,trace):
    self.psets = self.PSets(pset(),
                            pset(),
                            pset(),
                            pset())

    self.pmaps = self.PMaps(pmap(),
                            pmap(),
                            pmap(),
                            pmap())

    self.maps_to_constants = self.MapsToConstants(particle.numRequests.copy())
    self.maps_to_psets = self.MapsToPSets(particle.madeSPFamilies.copy(),particle.newChildren.copy())
    self.maps_to_clones = self.MapsToUniqueClones({ node => spaux.copy() for node,spaux in particle.madeSPAuxs })


######################### Persistent Sets
  def registerRandomChoice(self,node): self.rcs.add(node)
  def registerAEKernel(self,node): self.aes.add(node)
  def registerConstrainedChoice(self,node): self.ccs.add(node) # NOTE does not remove from rcs, commit() addresses this
  def registerRandomChoiceInScope(self,scope,block,node): self.sbns.add((scope,block,node))

######################### Persistent Maps to constants

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


######################## Persistent Maps to things that change through particle methods only

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

######################## Persistent Maps to things that change outside of particle methods

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
