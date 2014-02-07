from abc import ABCMeta
from value import VentureValue, SPRef, isVentureValue, asVentureValue

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

  def parents(self): return self.definiteParents()

class ConstantNode(Node):
  def __init__(self,value):
    super(ConstantNode,self).__init__()
    self.value = asVentureValue(value)

  def parents(self): return []
  def definiteParents(self): return []

class LookupNode(Node):
  def __init__(self,sourceNode):
    super(LookupNode,self).__init__()
    self.sourceNode = sourceNode

  def parents(self): return [self.sourceNode]
  def definiteParents(self): return [self.sourceNode]


class ApplicationNode(Node):
  __metaclass__ = ABCMeta

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
  def psp(self): return self.sp().requestPSP

class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,env):
    super(RequestNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.env = env
    self.outputNode = None

  def registerOutputNode(self,outputNode):
    self.outputNode = outputNode
    self.children.add(outputNode)

  def parents(self): return [self.operatorNode] + self.operandNodes
  def definiteParents(self): return [self.operatorNode] + self.operandNodes


class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode,env):
    super(OutputNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.requestNode = requestNode
    self.env = env

  def definiteParents(self): return [self.operatorNode] + self.operandNodes + [self.requestNode]
  def parents(self): return self.definiteParents() + self.esrParents

class Args(object):
  def __init__(self,trace,node):
    self.node = node
    self.operandValues = [trace.valueAt(operandNode) for operandNode in node.operandNodes]
    for v in self.operandValues:
      assert isVentureValue(v)
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode):
      self.requestValue = trace.valueAt(node.requestNode)
      self.esrValues = [trace.valueAt(esrParent) for esrParent in trace.esrParentsAt(node)]
      self.esrNodes = trace.esrParentsAt(node)
      self.madeSPAux = trace.madeSPAuxAt(node)
      self.isOutput = True

    self.spaux = trace.spauxAt(node)
    self.env = node.env

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)
