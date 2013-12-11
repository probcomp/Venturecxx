from abc import ABCMeta, abstractmethod

class Node():
  __metaclass__ = ABCMeta

class ConstantNode(Node):
  def __init__(self,value):
    self.value = value
    self.numRequests = 0
    self.children = set()
    self.madeSP = None
    self.madeSPAux = None

  def groundValue(self):
    if isinstance(self.value,SPRef): return self.value.makerNode.madeSP
    else: return self.value

  def parents(self): return []

class LookupNode(Node):
  def __init__(self,sourceNode):
    self.sourceNode = sourceNode
    sourceNode.children.add(self)
    self.value = sourceNode.value
    self.numRequests = 0
    self.children = set()

  def parents(self): return [self.sourceNode]

class ApplicationNode(Node):
  __metaclass__ = ABCMeta

  def args(self): return Args(self)
  def spRef(self): return self.operatorNode.value
  def sp(self): return self.spRef().makerNode.madeSP
  def spaux(self): return self.spRef().makerNode.madeSPAux

class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,env):
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.numRequests = 0
    self.env = env
    self.children = set()

  def psp(self): return self.sp().requestPSP

  def parents(self): return [self.operatorNode] + self.operandNodes

class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode,env):
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.requestNode = requestNode
    self.numRequests = 0
    self.esrParents = []
    self.env = env
    self.madeSP = None
    self.madeSPAux = None
    self.observedValue = None
    self.isObservation = False
    self.children = set()

  def observe(self,val):
    self.observedValue = val
    self.isObservation = True

  def psp(self): return self.sp().outputPSP

  def parents(self): return [self.operatorNode] + self.operandNodes + [self.requestNode] + self.esrParents

class Args():
  def __init__(self,node):
    self.node = node
    self.operandValues = [operandNode.value for operandNode in node.operandNodes]
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode):
      self.requestValue = node.request.value
      self.esrValues = [esrParent.value for esrParent in node.esrParents]
      self.esrParents = node.esrParents
      self.madeSPAux = node.madeSPAux
      self.isOutput = True

    self.spaux = node.spaux()
    self.env = node.env
