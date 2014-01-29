import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

class Particle(trace.Trace):
  # The trace is expected to be a torus, with the chosen scaffold
  # already detached.
  def __init__(self,trace):
    if type(trace) is Particle: initFromParticle(self,trace)
    elif type(trace) is Trace: initFromTrace(self,trace)
    else: raise Exception("Must init particle from trace or particle")

  # Note: using "copy()" informally for both legit_copy and persistent_copy
  def initFromParticle(self,particle):
    self.base = particle.base    

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
    self.madeSPAuxs = { node => spaux.copy() for node,spaux in particle.madeSPAuxs }

    # Category: Mutates explicitly
    # Data structures: legit_map to (changing) constants
    self.numRequests = particle.numRequests.copy()
    
    # Category: Expands monotonically explicitly
    # Data structures: legit_map to persistent set
    self.madeSPFamilies = particle.madeSPFamilies.copy()
    self.newChildren = particle.newChildren.copy()




