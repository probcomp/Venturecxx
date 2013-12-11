from builtin import builtInValues, builtInSPs

from env import Env

class Trace():
  def __init__(self):
    self.globalEnv = Env()
    for name,val in builtInValues():  globalEnv.addBinding(name,ConstantNode(val))
    for name,sp in builtInSPs():
      spNode = ConstantNode(sp)
      self.processMadeSP(spNode,False)
      assert spNode.value == spNode
      globalEnv.addBinding(name,spNode)

    self.rcs = [] # TODO make this an EasyEraseVector
    self.families = {}
    

  def registerAEKernel(self,node): pass
  def unregisterAEKernel(self,node): pass
  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.append(node)

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    del self.rcs[self.rcs.index(node)]

  def createConstantNode(self,val): return ConstantNode(exp)
  def createLookupNode(self,sourceNode): return LookupNode(sourceNode)
  def createApplicationNodes(self,operatorNode,operandNodes,env):
    requestNode = RequestNode(operatorNode,operandNodes,env)
    outputNode = OutputNode(operatorNode,operandNodes,requestNode,env)
    requestNode.children.add(outputNode)
    return outputNode

  def reconnectLookup(self,node,sourceNode): sourceNode.children.add(node)

  def registerBlock(self,block,subblock,esrParent): pass
  def unregisterBlock(self,block,subblock,esrParent): pass

  def addESREdge(self,esrParent,outputNode):
    esrParent.children.add(outputNode)
    outputNode.esrParents.append(esrParent)

  def popLastESRParent(self,outputNode):
    assert outputNode.esrParents
    esrParent = outputNode.esrParents.pop()
    esrParent.children.remove(outputNode)
    esrParent.numRequests -= 1
    return esrParent

