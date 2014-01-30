from builtin import builtInValues, builtInSPs
from env import Env
from node import ConstantNode,LookupNode,RequestNode,OutputNode,Args
import math
from regen import constrain,processMadeSP, evalFamily
from detach import unconstrain, teardownMadeSP, unevalFamily
from spref import SPRef
from scaffold import Scaffold
from infer import mixMH,MHOperator,MeanfieldOperator,BlockScaffoldIndexer,EnumerativeGibbsOperator,PGibbsOperator,ParticlePGibbsOperator
import random
from omegadb import OmegaDB
from smap import SMap
from sp import SPFamilies
from nose.tools import assert_equal,assert_is_not_none


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
    self.globalEnv = Env(self.globalEnv) # New frame so users can shadow globals

    self.rcs = set()
    self.ccs = set()
    self.aes = set()
    self.families = {}
    self.scopes = {} # :: {scope-name:smap{block-id:set(node)}}

  def registerAEKernel(self,node): self.aes.add(node)
  def unregisterAEKernel(self,node): self.aes.remove(node)

  def registerRandomChoice(self,node):
    assert not node in self.rcs
    self.rcs.add(node)
    self.registerRandomChoiceInScope("default",node,node)

  def registerRandomChoiceInScope(self,scope,block,node):
    if not scope in self.scopes: self.scopes[scope] = SMap()
    if not block in self.scopes[scope]: self.scopes[scope][block] = set()
    assert not node in self.scopes[scope][block]
    self.scopes[scope][block].add(node)
    assert not scope == "default" or len(self.scopes[scope][block]) == 1

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    self.rcs.remove(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def unregisterRandomChoiceInScope(self,scope,block,node):
    self.scopes[scope][block].remove(node)
    assert not scope == "default" or len(self.scopes[scope][block]) == 0
    if len(self.scopes[scope][block]) == 0: del self.scopes[scope][block]
    if len(self.scopes[scope]) == 0: del self.scopes[scope]

  def registerConstrainedChoice(self,node):
    self.ccs.add(node)
    self.unregisterRandomChoice(node)

  def unregisterConstrainedChoice(self,node):
    assert node in self.ccs
    self.ccs.remove(node)
    if self.pspAt(node).isRandom(): self.registerRandomChoice(node)

  def createConstantNode(self,val): return ConstantNode(val)
  def createLookupNode(self,sourceNode): 
    lookupNode = LookupNode(sourceNode)
    self.setValueAt(lookupNode,self.valueAt(sourceNode))
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

  def groundValueAt(self,node):
    value = self.valueAt(node)
    if isinstance(value,SPRef): return self.madeSPAt(value.makerNode)
    else: return value
      
  def argsAt(self,node): return Args(self,node)

  def spRefAt(self,node):
    candidate = self.valueAt(node.operatorNode)
    if not isinstance(candidate, SPRef):
      print "spRef not an spRef"
      print "is a: " + str(type(candidate))
      print node,node.operatorNode
    assert isinstance(candidate, SPRef)
    return candidate
  
  def spAt(self,node): return self.madeSPAt(self.spRefAt(node).makerNode)
  def spFamiliesAt(self,node): 
    spFamilies = self.madeSPFamiliesAt(self.spRefAt(node).makerNode)
    assert isinstance(spFamilies,SPFamilies)
    return spFamilies
  def spauxAt(self,node): return self.madeSPAuxAt(self.spRefAt(node).makerNode)
  def pspAt(self,node):
    if isinstance(node, RequestNode):
      return self.spAt(node).requestPSP
    else:
      assert isinstance(node, OutputNode)
      return self.spAt(node).outputPSP

  #### Stuff that a particle trace would need to override for persistence

  def valueAt(self,node):
    print "TRACE::VALUE_AT",node
    return node.value

  def setValueAt(self,node,value):
    node.value = value
    if value is None: print "TRACE::CLEAR_VALUE",node

  def madeSPAt(self,node): return node.madeSP
  def setMadeSPAt(self,node,sp): node.madeSP = sp
    
  def madeSPFamiliesAt(self,node):
    assert_is_not_none(node.madeSPFamilies)
    return node.madeSPFamilies

  def setMadeSPFamiliesAt(self,node,families): node.madeSPFamilies = families

  def madeSPAuxAt(self,node): return node.madeSPAux
  def setMadeSPAuxAt(self,node,aux): node.madeSPAux = aux

  def parentsAt(self,node): return node.parents()    
  def definiteParentsAt(self,node): return node.definiteParents()
            
  def esrParentsAt(self,node): return node.esrParents
  def setEsrParentsAt(self,node,parents): node.esrParents = parents
  def appendEsrParentAt(self,node,parent): node.esrParents.append(parent)
  def popEsrParentAt(self,node): return node.esrParents.pop()
    
  def childrenAt(self,node): return node.children
  def setChildrenAt(self,node,children): node.children = children
  def addChildAt(self,node,child): node.children.add(child)
  def removeChildAt(self,node,child): node.children.remove(child)
    
  def registerFamilyAt(self,node,esrId,esrParent): self.spFamiliesAt(node).registerFamily(esrId,esrParent)
  def unregisterFamilyAt(self,node,esrId): self.spFamiliesAt(node).unregisterFamily(esrId)
  def containsSPFamilyAt(self,node,esrId): return self.spFamiliesAt(node).containsFamily(esrId)
  def spFamilyAt(self,node,esrId): return self.spFamiliesAt(node).getFamily(esrId)
  def madeSPFamilyAt(self,node,esrId): return self.madeSPFamiliesAt(node).getFamily(esrId)

  def numRequestsAt(self,node): return node.numRequests
  def setNumRequestsAt(self,node,num): node.numRequests = num
  def incRequestsAt(self,node): node.numRequests += 1
  def decRequestsAt(self,node): node.numRequests -= 1

  def regenCountAt(self,scaffold,node): return scaffold.regenCounts[node]
  def incRegenCountAt(self,scaffold,node): scaffold.regenCounts[node] += 1
  def decRegenCountAt(self,scaffold,node): scaffold.regenCounts[node] -= 1 # need not be overriden
    
  def isConstrainedAt(self,node): return node in self.ccs
  
  #### For kernels
  def sampleBlock(self,scope): return self.scopes[scope].sample()[1]
  def logDensityOfBlock(self,scope): return -1 * math.log(self.numBlocksInScope(scope))
  def blocksInScope(self,scope): return self.scopes[scope].keys()
  def numBlocksInScope(self,scope): return len(self.blocksInScope(scope))
  def getAllNodesInScope(self,scope): return set.union(*self.scopes[scope].values())
  def getOrderedSetsInScope(self,scope): return self.scopes[scope].sortedValues()
  def getNodesInBlock(self,scope,block): return self.scopes[scope][block]


  def scopeHasEntropy(self,scope): 
    # right now scope in self.scopes iff it has entropy
    return scope in self.scopes and len(self.blocksInScope(scope)) > 0












  #### External interface to engine.py
  def eval(self,id,exp):
    assert not id in self.families
    (_,self.families[id]) = evalFamily(self,self.unboxExpression(exp),self.globalEnv,Scaffold(),OmegaDB(),{})
    
  def bindInGlobalEnv(self,sym,id): self.globalEnv.addBinding(sym,self.families[id])

  def extractValue(self,id): return self.boxValue(self.valueAt(self.families[id]))

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
  # "kernel" must be one of "mh" or "meanfield", and "transitions"
  # must be an integer.
  def infer(self,params):
    if not(self.scopeHasEntropy(params["scope"])):
      return
    for n in range(params["transitions"]):
      if params["kernel"] == "mh":
        assert params["with_mutation"]
        mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),MHOperator())
      elif params["kernel"] == "meanfield":
        assert params["with_mutation"]        
        mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),MeanfieldOperator(10,0.0001))
      elif params["kernel"] == "gibbs":
        assert params["with_mutation"]        
        mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),EnumerativeGibbsOperator())
      elif params["kernel"] == "pgibbs":
        if params["with_mutation"]:
          mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),PGibbsOperator(int(params["particles"])))
        else:
          mixMH(self,BlockScaffoldIndexer(params["scope"],params["block"]),ParticlePGibbsOperator(int(params["particles"])))          
      else: raise Exception("INFER (%s) MH is implemented" % params["kernel"])

      for node in self.aes: self.madeSPAt(node).AEInfer(self.madeSPAuxAt(node))

  def get_seed(self):
    # TODO Trace does not support seed control because it uses
    # Python's native randomness.
    return 0

  def getGlobalLogScore(self):
    # TODO Get the constrained nodes too
    return sum([self.pspAt(node).logDensity(self.groundValueAt(node),self.argsAt(node)) for node in self.rcs.union(self.ccs)])

  #### Helpers (shouldn't be class methods)

  # TODO temporary, probably need an extra layer of boxing for VentureValues
  # as in CXX
  def boxValue(self,val):
    if type(val) is str: return {"type":"symbol","value":val}
    elif type(val) is bool: return {"type":"boolean","value":val}
    elif type(val) is list: return {"type":"list","value":[self.boxValue(v) for v in val]}
    elif isinstance(val, SPRef): return {"type":"SP","value":val}
    else: return {"type":"number","value":val}


  def unboxValue(self,val): return val["value"]

  def unboxExpression(self,exp):
    if type(exp) == list: return [self.unboxExpression(subexp) for subexp in exp]
    else: return self.unboxValue(exp)

#################### Misc for particle commit

  def addNewMadeSPFamilies(self,node,newMadeSPFamilies):
    if node.madeSPFamilies is None: node.madeSPFamilies = {}
    for id,root in newMadeSPFamilies.iteritems():
      node.madeSPFamilies.registerFamily(id,root)

  def addNewChildren(self,node,newChildren): 
    for child in newChildren:
      node.children.add(child)
