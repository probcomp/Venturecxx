from builtin import builtInValues, builtInSPs
from env import Env
from node import ConstantNode,LookupNode,RequestNode,OutputNode
import math
from regen import constrain,processMadeSP, evalFamily
from detach import unconstrain, teardownMadeSP, unevalFamily
from spref import SPRef
from scaffold import Scaffold
import infer
import random
from omegadb import OmegaDB

class Trace(object):
  def __init__(self):
    self.gkernels = { ("mh",False) : infer.OutermostMixMHGKernel(self,infer.DetachAndRegenGKernel(self)) }
    self.globalEnv = Env()
    for name,val in builtInValues().iteritems():
      self.globalEnv.addBinding(name,ConstantNode(val))
    for name,sp in builtInSPs().iteritems():
      spNode = ConstantNode(sp)
      processMadeSP(self,spNode,False)
      assert isinstance(spNode.value, SPRef)
      self.globalEnv.addBinding(name,spNode)

    self.rcs = [] # TODO make this an EasyEraseVector
    self.aes = []
    self.families = {}

  def registerAEKernel(self,node): self.aes.append(node)
  def unregisterAEKernel(self,node): del self.aes[self.aes.index(node)]

  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.append(node)

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    del self.rcs[self.rcs.index(node)]

  def createConstantNode(self,val): return ConstantNode(val)
  def createLookupNode(self,sourceNode): 
    lookupNode = LookupNode(sourceNode)
    sourceNode.children.add(lookupNode)
    return lookupNode

  def createApplicationNodes(self,operatorNode,operandNodes,env):
    requestNode = RequestNode(operatorNode,operandNodes,env)
    outputNode = OutputNode(operatorNode,operandNodes,requestNode,env)
    operatorNode.children.add(requestNode)
    operatorNode.children.add(outputNode)
    for operandNode in operandNodes:
      operandNode.children.add(requestNode)
      operandNode.children.add(outputNode)
    requestNode.registerOutputNode(outputNode)
    return (requestNode,outputNode)

  def reconnectLookup(self,node,sourceNode): sourceNode.children.add(node)

  def registerBlock(self,block,subblock,esrParent): pass
  def unregisterBlock(self,block,subblock,esrParent): pass

  def addESREdge(self,esrParent,outputNode):
    esrParent.numRequests += 1
    esrParent.children.add(outputNode)
    outputNode.esrParents.append(esrParent)

  def popLastESRParent(self,outputNode):
    assert outputNode.esrParents
    esrParent = outputNode.esrParents.pop()
    esrParent.children.remove(outputNode)
    esrParent.numRequests -= 1
    return esrParent
  
  def disconnectLookup(self,lookupNode): lookupNode.sourceNode.children.remove(lookupNode)
  def reconnectLookup(self,lookupNode): lookupNode.sourceNode.children.add(lookupNode)

  #### Stuff that a particle trace would need to override for persistence
  def valueAt(self,node): return node.value
  def setValueAt(self,node,value): node.value = value
  def groundValueAt(self,node): return node.groundValue()
  def esrParentsAt(self,node): return node.esrParents
  def pspAt(self,node): return node.psp()
  def argsAt(self,node): return node.args()
  def unincorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.psp().unincorporate(node.groundValue(), node.args())
  def incorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.psp().incorporate(node.groundValue(), node.args())
  def logDensityAt(self,node,value):
    return node.psp().logDensity(value,node.args())

  #### For kernels
  def samplePrincipalNode(self): return random.choice(self.rcs)
  def logDensityOfPrincipalNode(self,principalNode): return -1 * math.log(len(self.rcs))

  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,self.unboxExpression(exp),self.globalEnv,Scaffold(),OmegaDB(),{})
    
  def bindInGlobalEnv(self,sym,id): self.globalEnv.addBinding(sym,self.families[id])

  def extractValue(self,id): return self.boxValue(self.families[id].value)

  def observe(self,id,val):
    node = self.families[id]
    node.observe(self.unboxValue(val))
    constrain(self,node,node.observedValue)

  def unobserve(self,id): unconstrain(self,self.families[id])

  def uneval(self,id):
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(),OmegaDB())
    del self.families[id]

  def continuous_inference_status(self): return {"running" : False}

  def infer(self,params): 
    if not params["kernel"] == "mh": raise Exception("INFER (%s) MH is implemented" % params["kernel"])
    if params["use_global_scaffold"]: raise Exception("INFER global scaffold not yet implemented")
    assert (params["kernel"],params["use_global_scaffold"]) in self.gkernels
    gkernel = self.gkernels[(params["kernel"],params["use_global_scaffold"])]
    gkernel.infer(params["transitions"])
    for node in self.aes: node.madeSP.AEInfer(node.madeSPAux)

  #### Helpers (shouldn't be class methods)

  # TODO temporary, probably need an extra layer of boxing for VentureValues
  # as in CXX
  def boxValue(self,val):
    if type(val) is str: return {"type":"symbol","value":val}
    elif type(val) is bool: return {"type":"boolean","value":val}
    elif type(val) is list: return {"type":"list","value":val}
    else: return {"type":"number","value":val}


  def unboxValue(self,val): return val["value"]

  def unboxExpression(self,exp):
    if type(exp) == list: return [self.unboxExpression(subexp) for subexp in exp]
    else: return self.unboxValue(exp)
