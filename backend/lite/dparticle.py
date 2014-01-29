import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

class Particle(trace.Trace):
  class PSets(object):
    def __init__(self,rcs,ccs,aes,sbns):
      self.rcs = rcs
      self.ccs = ccs
      self.aes = aes
      self.sbns = sbns

  class PMaps(object):
    def __init__(self,values,madeSPs,esrParents,regenCountBools):
      self.values = values
      self.madeSPs = madeSPs
      self.esrParents = esrParents
      self.regenCountBools = regenCountBools

  class MapsToConstants(object):
    def __init__(self,numRequests):
      self.numRequests = numRequests

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
                            particle.pmaps.regenCountBools)

    self.maps_to_constants = self.MapsToConstants(particle.numRequests.copy())
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

  
  def valueAt(self,node): 
    if node in self.values: return self.values[node]
    else: return self.base.valueAt(node)

  def setValueAt(self,node,value): 
    assert not node in self.values
    self.values[node] = value

  def madeSPAt(self,node):
    if node in self.madeSPs: return self.madeSPs[node]
    else: return self.base.madeSPAt(node)

  def setMadeSPAt(self,node,sp): 
    assert not node in self.madeSPs
    self.madeSPs[node] = sp

  def madeSPFamiliesAt(self,node):
    if node in self.madeSPFamilies: return self.madeSPFamilies[node]
    else: return self.base.madeSPFamiliesAt(node)

  def setMadeSPFamiliesAt(self,node,madeSPFamilyies):
    assert not node in self.madeSPFamilies
    self.madeSPFamilies[node] = madeSPFamilies

  def madeSPAuxAt(self,node):
    if node in self.madeSPAuxs: return self.madeSPAuxs[node]
    else: return self.base.madeSPFamiliesAt(node)
    
  def setMadeSPAuxAt(self,node,aux):
    assert not node in self.madeSPAuxs
    self.madeSPAuxs[node] = aux

  def esrParentsAt(self,node): 
    if node in self.esrParents: return self.esrParents[node]
    else: return self.base.esrParentsAt(node)

  def appendEsrParentAt(self,node,parent):
    if not node in self.esrParents: self.esrParents[node] = []
    self.esrParents[node].append(parent)

  def popEsrParentAt(self,node): raise Exception("Should not be called on a particle")
  def childrenAt(self,node): raise Exception("Should not be called on a particle")

  def addChildAt(self,node,child):
    if not node in self.newChildren: self.newChildren[node] = []
    self.newChildren[node].append(child)
  
  def removeChildAt(self,node,child): raise Exception("Should not be called on a particle")

  # TODO SUBTLE! Regular in trace, persistent for particles?
  # Think through this carefully
  def registerFamilyAt(self,node,esrId,esrParent): raise Exception("Not yet implemented!")

  def unregisterFamilyAt(self,node,esrId): raise Exception("Should not be called on a particle")

  def numRequestsAt(self,node):
    if node in self.numRequests: return self.numRequests[node]
    else: return self.base.numRequestsAt(node)
    
  def incRequestsAt(self,node):
    if not node in self.numRequests: self.numRequests[node] = self.base.numRequests[node]
    self.numRequests[node] += 1

  def decRequestsAt(self,node): raise Exception("Should not be called on a particle")

  def registerAEKernel(self,node):
    if not node in self.aes: self.aes = []
    self.aes.append(node)

  def unregisterAEKernel(self,node): raise Exception("Should not be called on a particle")

  def registerRandomChoice(self,node): self.rcs.add(node)
  def registerRandomChoiceInScope(self,scope,block,node): self.sbns.add((scope,block,node))

  def unregisterRandomChoice(self,node): raise Exception("Should not be called on a particle")
  def unregisterRandomChoiceInScope(self,scope,block,node): raise Exception("Should not be called on a particle")
  def registerConstrainedChoice(self,node): 
    self.ccs.add(node)
    self.rcs.remove(node)

  def unregisterConstrainedChoice(self,node): raise Exception("Should not be called on a particle")

  def regenCountAt(self,scaffold,node): 
    if not node in self.regenCounts: self.regenCounts[node] = 0
    return self.regenCounts[node]

  def incRegenCountAt(self,scaffold,node): 
    if not node in self.regenCounts: self.regenCounts[node] = 0
    self.regenCounts[node] += 1

  def decRegenCountAt(self,scaffold,node): raise Exception("Should never be called on a particle")

  # TODO subtle: 
  # How should we handle this bookkeeping?
  def numBlocksInScope(self,scope): raise Exception("Not yet implemented")

  # TODO 
  # iterate over every data structure, pushing the changes back to the trace
  def commit(self): raise Exception("Not yet implemented")
