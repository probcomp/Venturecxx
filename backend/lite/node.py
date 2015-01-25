from value import VentureValue, ExpressionType
from request import Request

class Node(object):
  def __init__(self, address):
    self.address = address
    self.value = None
    self.children = set()
    self.isObservation = False
    self.madeSPRecord = None
    self.aaaMadeSPAux = None
    self.numRequests = 0
    self.esrParents = []
    self.esrParents = []

  def observe(self,val):
    self.observedValue = val
    self.isObservation = True
    assert isinstance(val, VentureValue)

  def isAppropriateValue(self, value):
    return value is None or isinstance(value, VentureValue)

  def parents(self): return self.definiteParents()
  def definiteParents(self):
    raise Exception("Cannot compute the definite parents of an abstract node.")


class ConstantNode(Node):
  def __init__(self,address,value):
    super(ConstantNode,self).__init__(address)
    if isinstance(value, VentureValue):
      # Possible for programmatic construction, e.g. builtin.py
      # Will also occur for literal atoms, since there's no other way
      # to tell them apart from literal numbers.
      self.value = value
    else: # In eval
      self.value = ExpressionType().asVentureValue(value)

  def definiteParents(self): return []


class LookupNode(Node):
  def __init__(self,address,sourceNode):
    super(LookupNode,self).__init__(address)
    self.sourceNode = sourceNode

  def definiteParents(self): return [self.sourceNode]


class ApplicationNode(Node):
  def __init__(self, address, operatorNode, operandNodes):
    super(ApplicationNode, self).__init__(address)
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes


class RequestNode(ApplicationNode):
  def __init__(self,address,operatorNode,operandNodes,env):
    super(RequestNode,self).__init__(address, operatorNode, operandNodes)
    self.env = env
    self.outputNode = None

  def registerOutputNode(self,outputNode):
    self.outputNode = outputNode
    self.children.add(outputNode)

  def definiteParents(self): return [self.operatorNode] + self.operandNodes

  def isAppropriateValue(self, value):
    return value is None or isinstance(value, Request)


class OutputNode(ApplicationNode):
  def __init__(self,address,operatorNode,operandNodes,requestNode,env):
    super(OutputNode,self).__init__(address, operatorNode, operandNodes)
    self.requestNode = requestNode
    self.env = env
    self.isFrozen = False

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
      self.madeSPAux = trace.getAAAMadeSPAuxAt(node)
      self.isOutput = True
    else:
      self.isOutput = False

    self.spaux = trace.spauxAt(node)
    self.env = node.env

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)
