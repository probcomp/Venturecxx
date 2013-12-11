from abc import ABCMeta, abstractmethod

class Node():
  __metaclass__ = ABCMeta

class ConstantNode(Node):
  def __init__(self,value): 
    self.value = value
    self.numRequests = 0
    self.children = set()
  
  def parents(): return []

class LookupNode(Node):
  def __init__(self,sourceNode):
    self.sourceNode = sourceNode
    sourceNode.children.add(self)
    self.value = sourceNode.value
    self.numRequests = 0
    self.children = set()

  def parents(): return [self.sourceNode]

class ApplicationNode(Node):
  __metaclass__ = ABCMeta
  
  def spRef(): return self.operandNode.value
  def sp(): return self.spRef().madeSP
  def spaux(): return self.spRef().madeSPAux

class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes):
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.numRequests = 0
 
  def parents(): return [self.operatorNode] + self.operandNodes

class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode):
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.requestNode = requestNode
    self.numRequests = 0
    self.esrParents = []
    self.children = set()
    
  def parents(): return [self.operatorNode] + self.operandNodes + [self.requestNode] + self.esrParents
