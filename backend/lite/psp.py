from abc import ABCMeta, abstractmethod
from lkernel import DefaultAAALKernel,DefaultVariationalLKernel
from request import Request
import copy

class PSP(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,args): pass
  def logDensity(self,value,args): return 0
  def incorporate(self,value,args): pass
  def unincorporate(self,value,args): pass
  # Returns a Python list of VentureValue objects
  def enumerateValues(self,args): raise Exception("Cannot enumerate")
  def isRandom(self): return False
  def canAbsorb(self,trace,appNode,parentNode): return False

  def childrenCanAAA(self): return False
  def getAAALKernel(self): return DefaultAAALKernel(self)

  def makesHSRs(self): return False
  def canEnumerate(self): return False

  def hasVariationalLKernel(self): return False
  def getVariationalLKernel(self,trace,node): return DefaultVariationalLKernel(trace,self,node)

  def hasSimulationKernel(self): return False
  def hasDeltaKernel(self): return False

  def description(self,name): return None

class NullRequestPSP(PSP):
  def simulate(self,args): return Request()
  def canAbsorb(self,trace,appNode,parentNode): return True

class ESRRefOutputPSP(PSP):
  def simulate(self,args):
    assert len(args.esrNodes) ==  1
    return args.esrValues[0]

  def canAbsorb(self,trace,appNode,parentNode):
    return parentNode != trace.esrParentsAt(appNode)[0] and parentNode != appNode.requestNode

class RandomPSP(PSP):
  __metaclass__ = ABCMeta
  @abstractmethod
  def simulate(self,args): pass
  def isRandom(self): return True
  def canAbsorb(self,trace,appNode,parentNode): return True    

class TypedPSP(PSP):
  def __init__(self, args_types, return_type, psp, variadic=False):
    self.args_types = args_types
    self.return_type = return_type
    self.psp = psp
    self.variadic = variadic
    if variadic:
      assert len(args_types) == 1 # TODO Support non-homogeneous variadics later

  def wrap_return(self, value):
    return self.return_type.asVentureValue(value)
  def unwrap_return(self, value):
    return self.return_type.asPython(value)
  def unwrap_args(self, args):
    assert not args.esrValues # TODO Only support outputs that have no requesters
    answer = copy.copy(args)
    if not self.variadic:
      assert len(args.operandValues) == len(self.args_types)
      answer.operandValues = [self.args_types[i].asPython(args.operandValues[i]) for i in len(args.operandValues)]
    else:
      answer.operandValues = [self.args_types[0].asPython(v) for v in args.operandValues]

  def simulate(self,args):
    return self.wrap_return(self.psp.simulate(self.unwrap_args(args)))
  def logDensity(self,value,args):
    return self.psp.logDensity(self.unwrap_return(value), self.unwrap_args(args))
  def incorporate(self,value,args):
    return self.psp.incorporate(self.unwrap_return(value), self.unwrap_args(args))
  def unincorporate(self,value,args):
    return self.psp.unincorporate(self.unwrap_return(value), self.unwrap_args(args))
  def enumerateValues(self,args):
    return [self.wrap_return(v) for v in self.psp.enumerateValues(self.unwrap_args(args))]
  def isRandom(self):
    return self.psp.isRandom()
  def canAbsorb(self,trace,appNode,parentNode):
    return self.psp.canAbsorb(trace, appNode, parentNode)

  def childrenCanAAA(self):
    return self.psp.childrenCanAAA()
  def getAAALKernel(self):
    # TODO Is this right?  Or should I somehow wrap the AAA LKernel so
    # it deals with the types properly?
    return self.psp.getAAALKernel()

  def makesHSRs(self): return self.psp.makeHSRs()
  def canEnumerate(self): return self.psp.canEnumerate()

  def hasVariationalLKernel(self): return self.psp.hasVariationalLKernel()
  def getVariationalLKernel(self,trace,node):
    # TODO Is this right?  Or should I somehow wrap the variational
    # LKernel so it deals with the types properly?
    return self.psp.getVariationalLKernel(trace, node)

  def hasSimulationKernel(self): return self.psp.hasSimulationKernel()
  def hasDeltaKernel(self): return self.hasDeltaKernel()

  def description(self,name):
    # TODO Automatically add the type signature?
    return self.psp.description(name)
