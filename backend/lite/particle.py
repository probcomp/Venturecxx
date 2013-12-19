from trace import Trace

class Particle(Trace):
  def __init__(self,trace):
    self.base = trace
    self.cache = {} # TODO persistent map from nodes to node records

  def _at(self,node):
    return self.cache[node]

  def _alterAt(self,node,f):
    self.cache = self.cache.insert(node,f(self._at(node)))

  def valueAt(self,node):
    return self._at(node).value
  def setValueAt(self,node,value):
    self._alterAt(node, lambda r: r.update_value(value))
  def madeSPAt(self,node):
    return self._at(node).madeSP
  def setMadeSPAt(self,node,sp):
    self._alterAt(node, lambda r: r.update_madeSP(sp))
  def madeSPAuxAt(self,node):
    return self._at(node).madeSPAux
  def setMadeSPAuxAt(self,node,aux):
    self._alterAt(node, lambda r: r.update_madeSPAux(aux))
  def esrParentsAt(self,node):
    return self._at(node).esrParents
  def appendEsrParentAt(self,node,parent):
    self._alterAt(node, lambda r: r.append_esrParent(parent))
  def popEsrParentAt(self,node):
    ans = self._at(node).topEsrParent()
    self._alterAt(node, lambda r: r.pop_esrParent())
    return ans
  def parentsAt(self,node):
    return self._at(node).parents()
  def childrenAt(self,node):
    return self._at(node).children
  def addChildAt(self,node,child):
    self._alterAt(node, lambda r: r.add_child(child))
  def removeChildAt(self,node,child):
    self._alterAt(node, lambda r: r.remove_child(child))
  def registerFamilyAt(self,node,esrId,esrParent):
    self._alterAt(node, lambda r: r.registerFamily(esrId,esrParent))
  def unregisterFamilyAt(self,node,esrId):
    self._alterAt(node, lambda r: r.unregisterFamily(esrId))
  def numRequestsAt(self,node):
    return self._at(node).numRequests
  def incRequestsAt(self,node):
    self._alterAt(node, lambda r: r.incRequests)
  def decRequestsAt(self,node):
    self._alterAt(node, lambda r: r.decRequests)
