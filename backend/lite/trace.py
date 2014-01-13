from builtin import builtInValues, builtInSPs
from env import Env
from node import ConstantNode,LookupNode,RequestNode,OutputNode
import math
from regen import constrain,processMadeSP, evalFamily
from detach import unconstrain, teardownMadeSP, unevalFamily
from spref import SPRef
from scaffold import Scaffold
from infer import mixMH,MHOperator,MeanfieldOperator,BlockScaffoldIndexer
import random
from omegadb import OmegaDB

class Trace(object):
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
    self.aes = []
    self.families = {}
    self.scopes = {} # :: {(scope-name,block-id):set(node)}

  def registerAEKernel(self,node): self.aes.append(node)
  def unregisterAEKernel(self,node): del self.aes[self.aes.index(node)]

  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.append(node)
    for key in node.scopes.iteritems():
      if key in self.scopes:
        self.scopes[key].add(node)
      else:
        self.scopes[key] = set([node])

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    del self.rcs[self.rcs.index(node)]
    for key in node.scopes.iteritems():
      if key in self.scopes:
        self.scopes[key].remove(node)

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
  def madeSPAt(self,node): return node.madeSP
  def setMadeSPAt(self,node,sp): node.madeSP = sp
  def setMadeSPAux(self,node,aux): node.madeSPAux = aux
  def esrParentsAt(self,node): return node.esrParents
  def parentsAt(self,node): return node.parents()
  def childrenAt(self,node): return node.children
  def pspAt(self,node): return node.psp()
  def spAt(self,node): return node.sp()
  def spauxAt(self,node): return node.spaux()
  def argsAt(self,node): return node.args()
  def unincorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.psp().unincorporate(node.groundValue(), node.args())
  def incorporateAt(self,node):
    # TODO Should this really be groundValue and not value?
    return node.psp().incorporate(node.groundValue(), node.args())
  def logDensityAt(self,node,value):
    return node.psp().logDensity(value,node.args())
  def registerFamilyAt(self,node,esrId,esrParent):
    node.spaux().registerFamily(esrId,esrParent)
  def unregisterFamilyAt(self,node,esrId):
    node.spaux().unregisterFamily(esrId)

  def isConstrainedAt(self,node):
    # TODO keep track of ccs explicitly
    return self.pspAt(node).isRandom() and node not in self.rcs

  #### For kernels
  def samplePrincipalNode(self): return random.choice(self.rcs)
  def logDensityOfPrincipalNode(self,principalNode): return -1 * math.log(len(self.rcs))
  def sampleBlock(self,scope):
    # TODO Use a better data structure for this
    blocks = [blk for (sc,blk) in self.scopes.keys() if sc == scope]
    return random.choice(blocks)
  def logDensityOfBlock(self,scope,block):
    # TODO Use a better data structure for this
    blocks = [blk for (sc,blk) in self.scopes.keys() if sc == scope]
    return -1 * math.log(len(blocks))

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

  def numRandomChoices(self):
    return len(self.rcs)

  def continuous_inference_status(self): return {"running" : False}

  # params is a hash with keys "kernel", "scope", "block",
  # "transitions" (the latter should be named "repeats").  Right now,
  # "kernel" must be one of "mh" or "meanfield", "scope" must be
  # "default", "block" must be "one", and "transitions" must be an
  # integer.
  def infer(self,params):
    for n in range(params["transitions"]):
      if params["kernel"] == "mh": mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),MHOperator())
      elif params["kernel"] == "meanfield": mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),MeanfieldOperator(10,0.0001))
      else: raise Exception("INFER (%s) MH is implemented" % params["kernel"])

      for node in self.aes: node.madeSP.AEInfer(node.madeSPAux)

  #### Helpers (shouldn't be class methods)

  # TODO temporary, probably need an extra layer of boxing for VentureValues
  # as in CXX
  def boxValue(self,val):
    if type(val) is str: return {"type":"symbol","value":val}
    elif type(val) is bool: return {"type":"boolean","value":val}
    elif type(val) is list: return {"type":"list","value":[self.boxValue(v) for v in val]}
    else: return {"type":"number","value":val}


  def unboxValue(self,val): return val["value"]

  def unboxExpression(self,exp):
    if type(exp) == list: return [self.unboxExpression(subexp) for subexp in exp]
    else: return self.unboxValue(exp)
