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
    
    



    # Category: Sets that are monotonically increasing across particles
    # Data structures: persistent sets
    # Note: they may mutate within a particle (e.g. via constrain)
    self.rcs = particle.rcs.copy()
    self.ccs = particle.ccs.copy()
    self.aes = particle.aes.copy()
    self.scope_block_nodes = particles.scope_block_nodes.copy() # set { (scope,block,node) }

    # Category: Monotonically increasing maps from nodes to constants (no mutation across particles)
    # Data structures: persistent map { node => constant }
    self.regenCountBools = particle.regenCountBools.copy() # persistent
    self.values = particle.values.copy()
    self.madeSPs = particle.madeSPs.copy()
    self.esrParents = particle.esrParents.copy()

    # Category: Mutates in other places
    # Data structures: legit_map, where we deep copy upon each extension
    self.madeSPAuxs = 

    # Category: Mutates explicitly
    # Data structures: legit_map to (changing) constants
    self.numRequests = particle.numRequests.copy()
    
    # Category: Expands monotonically explicitly
    # Data structures: legit_map to persistent set
    self.madeSPFamilies = particle.madeSPFamilies.copy()
    self.newChildren = particle.newChildren.copy()




