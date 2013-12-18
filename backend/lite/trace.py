from builtin import builtInValues, builtInSPs
from env import Env
from node import ConstantNode,LookupNode,RequestNode,OutputNode
import math
from regen import constrain,processMadeSP, evalFamily
from detach import unconstrain, teardownMadeSP, unevalFamily
from spref import SPRef
from scaffold import Scaffold
from infer import MHInfer
import random
from omegadb import OmegaDB

class Trace(object):
  def __init__(self):

    self.globalEnv = Env()
    for name,val in builtInValues().iteritems():
      self.globalEnv.addBinding(name,ConstantNode(val))
    for name,sp in builtInSPs().iteritems():
      spNode = self.createConstantNode(sp)
      processMadeSP(self,spNode,False)
      assert isinstance(self.valueAt(spNode), SPRef)
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
    self.addChildAt(sourceNode,lookupNode)
    return lookupNode

  def createApplicationNodes(self,operatorNode,operandNodes,env):
    requestNode = RequestNode(operatorNode,operandNodes,env)
    outputNode = OutputNode(operatorNode,operandNodes,requestNode,env)
    self.addChildAt(operatorNode,requestNode)
    self.addChildAt(operatorNode,outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode,requestNode)
      self.addChildAt(operandNode,outputNode)
    requestNode.registerOutputNode(outputNode)
    return (requestNode,outputNode)

  def reconnectLookup(self,node,sourceNode): sourceNode.children.add(node)

  def registerBlock(self,block,subblock,esrParent): pass
  def unregisterBlock(self,block,subblock,esrParent): pass

  def addESREdge(self,esrParent,outputNode):
    self.incRequestsAt(esrParent)
    self.addChildAt(esrParent,outputNode)
    self.appendEsrParentAt(outputNode,esrParent)

  def popLastESRParent(self,outputNode):
    assert self.esrParentsAt(outputNode)
    esrParent = self.popEsrParentAt(outputNode)
    self.removeChildAt(esrParent,outputNode)
    self.decRequestsAt(esrParent)
    return esrParent
  
  def disconnectLookup(self,lookupNode):
    self.removeChildAt(lookupNode.sourceNode,lookupNode)
  def reconnectLookup(self,lookupNode):
    self.addChildAt(lookupNode.sourceNode,lookupNode)

  #### Stuff that a particle trace would need to override for persistence
  def valueAt(self,node): return node.Tvalue
  def setValueAt(self,node,value): node.Tvalue = value
  def groundValueAt(self,node): return node.TgroundValue()
  def madeSPAt(self,node): return node.TmadeSP
  def setMadeSPAt(self,node,sp): node.TmadeSP = sp
  def madeSPAuxAt(self,node): return node.TmadeSPAux
  def setMadeSPAuxAt(self,node,aux): node.TmadeSPAux = aux
  def esrParentsAt(self,node): return node.TesrParents
  def appendEsrParentAt(self,node,parent): node.TesrParents.append(parent)
  def popEsrParentAt(self,node): return node.TesrParents.pop()
  def parentsAt(self,node): return node.Tparents()
  def childrenAt(self,node): return node.Tchildren
  def addChildAt(self,node,child): node.Tchildren.add(child)
  def removeChildAt(self,node,child): node.Tchildren.remove(child)
  def pspAt(self,node): return node.Tpsp()
  def spAt(self,node): return node.Tsp()
  def spauxAt(self,node): return node.Tspaux()
  def argsAt(self,node): return node.Targs()
  def unincorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.Tpsp().unincorporate(node.TgroundValue(), node.Targs())
  def incorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.Tpsp().incorporate(node.TgroundValue(), node.Targs())
  def logDensityAt(self,node,value):
    return node.Tpsp().logDensity(value,node.Targs())
  def registerFamilyAt(self,node,esrId,esrParent):
    node.Tspaux().registerFamily(esrId,esrParent)
  def unregisterFamilyAt(self,node,esrId):
    node.Tspaux().unregisterFamily(esrId)
  def numRequestsAt(self,node): return node.TnumRequests
  def incRequestsAt(self,node): node.TnumRequests += 1
  def decRequestsAt(self,node): node.TnumRequests -= 1

  #### For kernels
  def samplePrincipalNode(self): return random.choice(self.rcs)
  def logDensityOfPrincipalNode(self,principalNode): return -1 * math.log(len(self.rcs))

  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,self.unboxExpression(exp),self.globalEnv,Scaffold(self),OmegaDB(),{})
    
  def bindInGlobalEnv(self,sym,id): self.globalEnv.addBinding(sym,self.families[id])

  def extractValue(self,id): return self.boxValue(self.valueAt(self.families[id]))

  def observe(self,id,val):
    node = self.families[id]
    node.observe(self.unboxValue(val))
    constrain(self,node,node.observedValue)

  def unobserve(self,id): unconstrain(self,self.families[id])

  def uneval(self,id):
    assert id in self.families
    unevalFamily(self,self.families[id],Scaffold(self),OmegaDB())
    del self.families[id]

  def continuous_inference_status(self): return {"running" : False}

  def infer(self,params): 
    if not params["kernel"] == "mh": raise Exception("INFER (%s) MH is implemented" % params["kernel"])
    if params["use_global_scaffold"]: raise Exception("INFER global scaffold not yet implemented")

    for n in range(params["transitions"]): MHInfer(self)
    for node in self.aes: self.madeSPAt(node).AEInfer(self.madeSPAuxAt(node))

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
