from builtin import builtInValues, builtInSPs
from env import Env
from node import *
from eval import processMadeSP
from spref import SPRef

class Trace():
  def __init__(self):
    self.globalEnv = Env()
    for name,val in builtInValues().iteritems():
      self.globalEnv.addBinding(name,ConstantNode(val))
    for name,sp in builtInSPs().iteritems():
      spNode = ConstantNode(sp)
      processMadeSP(self,spNode,False)
      assert isinstance(spNode.value, SPRef)
      self.globalEnv.addBinding(name,spNode)

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

  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,id,exp,self.globalEnv,Scaffold(),OmegaDB(),{})
    
  def bindInGlobalEnv(self,sym,id): self.globalEnv.addBinding(sym,self.families[id])

  def extractValue(self,id): return self.families[id].value

  def observe(self,id,val):
    node = self.families[id]
    node.observe(val)
    constrain(self,node)

  def unobserve(self,id): unconstrain(self,self.families[id])

  def uneval(self,id):
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(),OmegaDB())
    del self.families[id]

  def continuous_inference_status(self): return {"running" : False}

  def infer(self,params): raise Exception("INFER not implemented yet")
