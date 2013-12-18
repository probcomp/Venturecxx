from abc import ABCMeta, abstractmethod
from spref import SPRef

class Node(object):
  __metaclass__ = ABCMeta
  def __init__(self):
    self.Tvalue = None
    self.Tchildren = set()
    self.isObservation = False
    self.TmadeSP = None
    self.TmadeSPAux = None
    self.TnumRequests = 0
    self.isObservation = False

  def observe(self,val):
    self.observedValue = val
    self.isObservation = True

  def TgroundValue(self):
    if isinstance(self.Tvalue,SPRef): return self.Tvalue.makerNode.TmadeSP
    else: return self.Tvalue

class ConstantNode(Node):
  def __init__(self,value):
    super(ConstantNode,self).__init__()
    self.Tvalue = value

  def Tparents(self): return []


class LookupNode(Node):
  def __init__(self,sourceNode):
    super(LookupNode,self).__init__()
    self.sourceNode = sourceNode

  def Tparents(self): return [self.sourceNode]


class ApplicationNode(Node):
  __metaclass__ = ABCMeta

  def TspRef(self):
    if not isinstance(self.operatorNode.Tvalue,SPRef):
      print "spRef not an spRef"
      print "is a: " + str(type(self.operatorNode.Tvalue))
    assert isinstance(self.operatorNode.Tvalue,SPRef)
    return self.operatorNode.Tvalue

  def Tsp(self): return self.TspRef().makerNode.TmadeSP
  def Tspaux(self): return self.TspRef().makerNode.TmadeSPAux

class RequestNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,env):
    super(RequestNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.env = env
    self.outputNode = None

  def registerOutputNode(self,outputNode):
    self.outputNode = outputNode
    self.Tchildren.add(outputNode)

  def Tpsp(self): return self.Tsp().requestPSP

  def Tparents(self): return [self.operatorNode] + self.operandNodes

class OutputNode(ApplicationNode):
  def __init__(self,operatorNode,operandNodes,requestNode,env):
    super(OutputNode,self).__init__()
    self.operatorNode = operatorNode
    self.operandNodes = operandNodes
    self.requestNode = requestNode
    self.TesrParents = []
    self.env = env

  def Tpsp(self): return self.Tsp().outputPSP

  def Tparents(self): return [self.operatorNode] + self.operandNodes + [self.requestNode] + self.TesrParents

class Args():
  def __init__(self,trace,node):
    self.node = node
    self.operandValues = [trace.valueAt(operandNode) for operandNode in node.operandNodes]
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode):
      self.requestValue = trace.valueAt(node.requestNode)
      self.esrValues = [trace.valueAt(esrParent) for esrParent in trace.esrParentsAt(node)]
      self.esrNodes = trace.esrParentsAt(node)
      self.madeSPAux = trace.madeSPAuxAt(node)
      self.isOutput = True

    self.spaux = trace.spauxAt(node)
    self.env = node.env
