import copy
import math
from sp import SPFamilies
from nose.tools import assert_equal
import trace

class Particle(trace.Trace):
  # The trace is expected to be a torus, with the chosen scaffold
  # already detached.
  def __init__(self,trace=None,particle=None):
    if trace is not None:
      assert particle is None
      self.base = trace
      self.cache = {} # TODO persistent map from nodes to node records
      self.rcs = set() # TODO persistent set?
      self.ccs = set()
      self.aes = set()
      self.scopes = {}
      self.regenCounts = {}
    elif particle is not None:
      self.base = particle.base
      self.cache = particle.cache.copy() # TODO persistent map from nodes to node records
      self.rcs = particle.rcs.copy() # TODO persistent set?
      self.ccs = particle.ccs.copy()
      self.aes = particle.aes.copy()
      self.scopes = particle.scopes.copy()
      self.regenCounts = particle.regenCounts.copy()
    else:
      raise Exception("Particle has no default constructor")

  def _at(self,node):
    if node in self.cache:
      return self.cache[node]
    else:
      return record_for(node)

  def _alterAt(self,node,f):
    # self.cache = self.cache.insert(node,f(self._at(node)))
    self.cache[node] = f(self._at(node))

  def _ensure_spaux_cached(self,node):
    if node in self.cache: pass # OK
    else: self.cache[node] = self._at(node)

  def valueAt(self,node):
    value = self._at(node).value
    return value
  def setValueAt(self,node,value):
    self._alterAt(node, lambda r: r.update(value=value))
  def madeSPAt(self,node):
    return self._at(node).madeSP
  def setMadeSPAt(self,node,sp):
    self._alterAt(node, lambda r: r.update(madeSP=sp))

  def madeSPFamiliesAt(self,node): return self._at(node).madeSPFamilies
  def setMadeSPFamiliesAt(self,node,madeSPFamilies):     
    self._alterAt(node, lambda r: r.update(madeSPFamilies=madeSPFamilies))

  def madeSPAuxAt(self,node):
    return self._at(node).madeSPAux
  def setMadeSPAuxAt(self,node,aux):
    self._alterAt(node, lambda r: r.update(madeSPAux=aux))
  def esrParentsAt(self,node):
    return self._at(node).esrParents
  def appendEsrParentAt(self,node,parent):
    self._alterAt(node, lambda r: r.append_esrParent(parent))
  def popEsrParentAt(self,node):
    ans = self._at(node).top_esrParent()
    self._alterAt(node, lambda r: r.pop_esrParent())
    return ans
  def childrenAt(self,node):
    return self._at(node).children
  def addChildAt(self,node,child):
    self._alterAt(node, lambda r: r.add_child(child))
  def removeChildAt(self,node,child):
    self._alterAt(node, lambda r: r.remove_child(child))
  def registerFamilyAt(self,node,esrId,esrParent):
    self._alterAt(self.spRefAt(node).makerNode, lambda r: r.registerFamily(esrId,esrParent))
  def unregisterFamilyAt(self,node,esrId):
    self._alterAt(self.spRefAt(node).makerNode, lambda r: r.unregisterFamily(esrId))
  def unincorporateAt(self,node):
    self._ensure_spaux_cached(node)
    self._ensure_spaux_cached(self.spRefAt(node).makerNode)
    super(Particle, self).unincorporateAt(node)
  def incorporateAt(self,node):
    self._ensure_spaux_cached(node)
    self._ensure_spaux_cached(self.spRefAt(node).makerNode)
    super(Particle, self).incorporateAt(node)
  def numRequestsAt(self,node):
    return self._at(node).numRequests
  def incRequestsAt(self,node):
    self._alterAt(node, lambda r: r.update(numRequests = r.numRequests + 1))
  def decRequestsAt(self,node):
    self._alterAt(node, lambda r: r.update(numRequests = r.numRequests - 1))


  def registerAEKernel(self,node): self.aes.add(node)
  def unregisterAEKernel(self,node): self.aes.remove(node)

  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.add(node)
    self.registerRandomChoiceInScope("default",node,node)

  def registerRandomChoiceInScope(self,scope,block,node):
    if not scope in self.scopes: self.scopes[scope] = {}
    if not block in self.scopes[scope]:
      if scope in self.base.scopes and block in self.base.scopes[scope]:
        self.scopes[scope][block] = self.base.scopes[scope][block].copy()
      else: self.scopes[scope][block] = set()
    assert not node in self.scopes[scope][block]
    self.scopes[scope][block].add(node)
    assert not scope == "default" or len(self.scopes[scope][block]) == 1

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def unregisterRandomChoiceInScope(self,scope,block,node):
    self.scopes[scope][block].remove(node)
    assert not scope == "default" or len(self.scopes[scope][block]) == 0
    if len(self.scopes[scope][block]) == 0: del self.scopes[scope][block]
    if len(self.scopes[scope]) == 0: del self.scopes[scope]

  def registerConstrainedChoice(self,node):
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def unregisterConstrainedChoice(self,node):
    assert node in self.ccs
    self.ccs.remove(node)
    if self.pspAt(node).isRandom(): self.registerRandomChoice(node)

  def regenCountAt(self,scaffold,node):
    if not node in self.regenCounts: self.regenCounts[node] = 0
    return self.regenCounts[node]
  
  def incRegenCountAt(self,scaffold,node): self.regenCounts[node] += 1
  def decRegenCountAt(self,scaffold,node): self.regenCounts[node] -= 1 # need not be overriden

  def blocksInScope(self,scope):
    blocks = set()
    if scope in self.base.scopes: blocks.update(self.base.scopes[scope].keys())
    if scope in self.scopes: blocks.update(self.scopes[scope].keys())
    return blocks

  def commit(self):
    for (node,r) in self.cache.iteritems(): 
      print "comitting record..."
      r.commit(self.base, node)
    self.base.rcs.update(self.rcs)
    self.base.ccs.update(self.ccs)
    self.base.aes.update(self.aes)
    for scope in self.scopes:
      for block in self.scopes[scope].keys():
        for node in self.scopes[scope][block]:
          self.base.registerRandomChoiceInScope(scope,block,node)

def record_for(node):
  madeAux = None
  if node.madeSPAux is not None:
    madeAux = node.madeSPAux.copy()
    assert_equal(type(madeAux),type(node.madeSPAux))
  madeFamilies = None
  if node.madeSPFamilies is not None:
    madeFamilies = node.madeSPFamilies.copy()
  return Record(value=copy.copy(node.value), madeSP=node.madeSP, madeSPFamilies=madeFamilies,madeSPAux=madeAux,
                esrParents=copy.copy(node.esrParents), children=node.children.copy(), numRequests=node.numRequests)

class Record(object):
  def __init__(self,value=None,madeSP=None,madeSPFamilies=None,madeSPAux=None,esrParents=None,children=None,numRequests=0):
    self.value = value
    self.madeSP = madeSP
    self.madeSPFamilies = madeSPFamilies
    self.madeSPAux = madeSPAux
    self.esrParents = []
    if esrParents: self.esrParents = esrParents
    self.children = set()
    if children: self.children = children
    self.numRequests = numRequests

  def _copy(self):
    return Record(self.value, self.madeSP, self.madeSPFamilies,self.madeSPAux, self.esrParents, self.children, self.numRequests)

  def update(self,value=None,madeSP=None,madeSPFamilies=None,madeSPAux=None,esrParents=None,children=None,numRequests=None):
    ans = self._copy()
    if value is not None: ans.value = value
    if madeSP is not None: ans.madeSP = madeSP
    if madeSPFamilies is not None: ans.madeSPFamilies = madeSPFamilies
    if madeSPAux is not None: ans.madeSPAux = madeSPAux
    if esrParents is not None: ans.esrParents = esrParents
    if children is not None: ans.children = children
    if numRequests is not None: ans.numRequests = numRequests
    return ans

  def add_child(self,child):
    new_children = copy.copy(self.children)
    new_children.add(child)
    return self.update(children=new_children)

  def remove_child(self,child):
    new_children = copy.copy(self.children)
    new_children.remove(child)
    return self.update(children=new_children)

  def top_esrParent(self):
    return self.esrParents[-1]

  def pop_esrParent(self):
    new_esrParents = copy.copy(self.esrParents)
    new_esrParents.pop()
    return self.update(esrParents=new_esrParents)

  def append_esrParent(self,parent):
    new_esrParents = copy.copy(self.esrParents)
    new_esrParents.append(parent)
    return self.update(esrParents=new_esrParents)

  def registerFamily(self,esrId,esrParent):
    self.madeSPFamilies.registerFamily(esrId,esrParent)
    return self

  def unregisterFamily(self,esrId):
    self.madeSPFamilies.unregisterFamily(esrId)
    return self

  def commit(self,trace,node):
    if self.value is not None: trace.setValueAt(node,self.value)
    if self.madeSP is not None: trace.setMadeSPAt(node,self.madeSP)
    if self.madeSPFamilies is not None: trace.setMadeSPFamiliesAt(node,self.madeSPFamilies)
    if self.madeSPAux is not None: 
      print "committing aux..."
      trace.setMadeSPAuxAt(node,self.madeSPAux)
    if self.esrParents is not None: trace.setEsrParentsAt(node,self.esrParents)
    if self.children is not None: trace.setChildrenAt(node,self.children)
    if self.numRequests is not None: trace.setNumRequestsAt(node,self.numRequests)
