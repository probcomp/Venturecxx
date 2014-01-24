from abc import ABCMeta, abstractmethod
from spref import SPRef
from sp import SP
from scope import mergeWith

class Node(object):
  __metaclass__ = ABCMeta
  def __init__(self):
    self.value = None
    self.children = set()
    self.isObservation = False
    self.madeSP = None
    self.madeSPAux = None
    self.numRequests = 0
    self.isObservation = False
    self.esrParents = []

  def observe(self,val):
    self.observedValue = val
    self.isObservation = True

  def groundValue(self):
    if isinstance(self.value,SPRef): return self.value.makerNode.madeSP
    else: return self.value

  def parents(self): return self.definiteParents()


class ConstantNode(Node):
  def __init__(self,value):
    super(ConstantNode,self).__init__()
    self.value = value

  def definiteParents(self): return []

class LookupNode(Node):
  def __init__(self,sourceNode):
    super(LookupNode,self).__init__()
    self.sourceNode = sourceNode
    self.value = sourceNode.value

  def definiteParents(self): return [self.sourceNode]

class ApplicationNode(Node):
  __metaclass__ = ABCMeta

  def args(self): return Args(self)
  def spRef(self): 
    if not isinstance(self.operatorNode.value,SPRef):
      print "spRef not an spRef"
      print "is a: " + str(type(self.operatorNode.value))
    assert isinstance(self.operatorNode.value,SPRef)
    assert isinstance(self.operatorNode.value.makerNode,Node)
    assert not self.operatorNode.value.makerNode.madeSP is None
    assert isinstance(self.operatorNode.value.makerNode.madeSP,SP)
    return self.operatorNode.value

  def sp(self): return self.spRef().makerNode.madeSP
  def spaux(self): return self.spRef().makerNode.madeSPAux
  def addScope(self,scope):
    def valMerge(v1, v2):
      if not(v1 == v2):
        raise Exception("Assigning one node to two blocks in the same scope")
      else:
        return v1
    self.scopes = mergeWith(self.scopes, scope, valMerge)

class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,env):
    super(RequestNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.env = env
    self.outputNode = None
    self.scopes = {}

  def registerOutputNode(self,outputNode):
    self.outputNode = outputNode
    self.children.add(outputNode)

  def psp(self): return self.sp().requestPSP

  def definiteParents(self): return [self.operatorNode] + self.operandNodes

class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode,env):
    super(OutputNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.requestNode = requestNode
    self.env = env
    self.scopes = {}

  def psp(self): return self.sp().outputPSP

  def definiteParents(self): return [self.operatorNode] + self.operandNodes + [self.requestNode]
  def parents(self): return self.definiteParents() + self.esrParents

class Args():
  def __init__(self,node):
    self.node = node
    self.operandValues = [operandNode.value for operandNode in node.operandNodes]
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode):
      self.requestValue = node.requestNode.value
      self.esrValues = [esrParent.value for esrParent in node.esrParents]
      self.esrNodes = node.esrParents
      self.madeSPAux = node.madeSPAux
      self.isOutput = True

    self.spaux = node.spaux()
    self.env = node.env

