from abc import ABCMeta, abstractmethod
from value import VentureValue, SPRef, ExpressionType
from request import Request

class Node(object):
  __metaclass__ = ABCMeta
  def __init__(self):
    self.value = None
    self.children = set()
    self.isObservation = False
    self.madeSP = None
    self.madeSPFamilies = None
    self.madeSPAux = None
    self.numRequests = 0
    self.esrParents = []
    self.isObservation = False
    self.esrParents = []

  def observe(self,val):
    self.observedValue = val
    self.isObservation = True
    assert isinstance(val, VentureValue)

  def groundValue(self):
    if isinstance(self.value,SPRef): return self.value.makerNode.madeSP
    else: return self.value

  def isAppropriateValue(self, value):
    return value is None or isinstance(value, VentureValue)

  def parents(self): return self.definiteParents()
  @abstractmethod
  def definiteParents(self): pass

class ConstantNode(Node):
  def __init__(self,value):
    super(ConstantNode,self).__init__()
    if isinstance(value, VentureValue):
      # Possible for programmatic construction, e.g. builtin.py
      # Will also occur for literal atoms, since there's no other way
      # to tell them apart from literal numbers.
      self.value = value
    else: # In eval
      self.value = ExpressionType().asVentureValue(value)

  def definiteParents(self): return []


class LookupNode(Node):
  def __init__(self,sourceNode):
    super(LookupNode,self).__init__()
    self.sourceNode = sourceNode

  def definiteParents(self): return [self.sourceNode]


class ApplicationNode(Node):
  __metaclass__ = ABCMeta

  def __init__(self, operatorNode, operandNodes):
    super(ApplicationNode, self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes


class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,env):
    super(RequestNode,self).__init__(operatorNode, operandNodes)
    self.env = env
    self.outputNode = None

  def registerOutputNode(self,outputNode):
    self.outputNode = outputNode
    self.children.add(outputNode)

  def definiteParents(self): return [self.operatorNode] + self.operandNodes

  def isAppropriateValue(self, value):
    return value is None or isinstance(value, Request)


class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode,env):
    super(OutputNode,self).__init__(operatorNode, operandNodes)
    self.requestNode = requestNode
    self.env = env

  def definiteParents(self): return [self.operatorNode] + self.operandNodes + [self.requestNode]
  def parents(self): return self.definiteParents() + self.esrParents


class Args(object):
  def __init__(self,trace,node):
    self.node = node
    self.operandValues = [trace.valueAt(operandNode) for operandNode in node.operandNodes]
    for v in self.operandValues:
      # v could be None if this is for logDensityBound for rejection
      # sampling, which is computed from the torus.
      assert v is None or isinstance(v, VentureValue)
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode):
      self.requestValue = trace.valueAt(node.requestNode)
      self.esrValues = [trace.valueAt(esrParent) for esrParent in trace.esrParentsAt(node)]
      self.esrNodes = trace.esrParentsAt(node)
      self.madeSPAux = trace.madeSPAuxAt(node)
      self.isOutput = True
    else:
      self.isOutput = False

    self.spaux = trace.spauxAt(node)
    self.env = node.env

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)
