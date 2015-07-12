# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from value import VentureValue
from types import ExpressionType
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
    self.isFrozen = False

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


def isConstantNode(thing):
  return isinstance(thing, ConstantNode) or (isinstance(thing, Node) and thing.isFrozen)
def isLookupNode(thing):
  return isinstance(thing, LookupNode) and not thing.isFrozen
def isApplicationNode(thing):
  return isinstance(thing, ApplicationNode) and not thing.isFrozen
def isRequestNode(thing):
  return isinstance(thing, RequestNode) and not thing.isFrozen
def isOutputNode(thing):
  return isinstance(thing, OutputNode) and not thing.isFrozen

def Args(trace, node): # TODO Inline this shim for preserving this module's visible API
  if isinstance(node, OutputNode):
    return OutputArgs(trace, node)
  else:
    return RequestArgs(trace, node)

class RequestArgs(object):
  def __init__(self, trace, node):
    self.node = node
    self.operandValues = [trace.valueAt(operandNode) for operandNode in node.operandNodes]
    for v in self.operandValues:
      # v could be None if this is for logDensityBound for rejection
      # sampling, which is computed from the torus.
      assert v is None or isinstance(v, VentureValue)
    self.operandNodes = node.operandNodes
    self.isOutput = False
    self.spaux = trace.spauxAt(node)
    self.env = node.env

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)

class OutputArgs(RequestArgs):
  def __init__(self, trace, node):
    super(OutputArgs, self).__init__(trace, node)
    self.requestValue = trace.valueAt(node.requestNode)
    self.esrValues = [trace.valueAt(esrParent) for esrParent in trace.esrParentsAt(node)]
    self.esrNodes = trace.esrParentsAt(node)
    self.madeSPAux = trace.getAAAMadeSPAuxAt(node)
    self.isOutput = True
