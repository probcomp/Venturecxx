from abc import ABCMeta, abstractmethod
from lkernel import DefaultAAALKernel,DefaultVariationalLKernel,LKernel
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

class FunctionType(object): # TODO make this a VentureType?  With conversions!?
  """An object loosely representing a Venture function type.  It knows
the types expected for the arguments and the return, and thus knows
how to wrap and unwrap individual values or Args objects.  This is
used in the implementation of TypedPSP and TypedAAALKernel."""
  def __init__(self, args_types, return_type, variadic=False, min_req_args=None):
    self.args_types = args_types
    self.return_type = return_type
    self.variadic = variadic
    if variadic:
      assert len(args_types) == 1 # TODO Support non-homogeneous variadics later
    self.min_req_args = len(args_types) if min_req_args is None else min_req_args

  def wrap_return(self, value):
    return self.return_type.asVentureValue(value)
  def unwrap_return(self, value):
    if value is None:
      # Could happen for e.g. a "delta kernel" that is expected, by
      # e.g. pgibbs, to actually be a simulation kernel
      return None
    else:
      return self.return_type.asPython(value)
  def unwrap_args(self, args):
    if args.isOutput:
      assert not args.esrValues # TODO Later support outputs that have non-latent requesters
    answer = copy.copy(args)
    if not self.variadic:
      assert len(args.operandValues) >= self.min_req_args
      assert len(args.operandValues) <= len(self.args_types)
      answer.operandValues = [self.args_types[i].asPython(v) for (i,v) in enumerate(args.operandValues)]
    else:
      answer.operandValues = [self.args_types[0].asPython(v) for v in args.operandValues]
    return answer

class TypedPSP(PSP):
  def __init__(self, args_types, return_type, psp, variadic=False, min_req_args=None):
    self.f_type = FunctionType(args_types, return_type, variadic=variadic, min_req_args=min_req_args)
    self.psp = psp

  def simulate(self,args):
    return self.f_type.wrap_return(self.psp.simulate(self.f_type.unwrap_args(args)))
  def logDensity(self,value,args):
    return self.psp.logDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def incorporate(self,value,args):
    return self.psp.incorporate(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def unincorporate(self,value,args):
    return self.psp.unincorporate(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def enumerateValues(self,args):
    return [self.f_type.wrap_return(v) for v in self.psp.enumerateValues(self.f_type.unwrap_args(args))]
  def isRandom(self):
    return self.psp.isRandom()
  def canAbsorb(self,trace,appNode,parentNode):
    return self.psp.canAbsorb(trace, appNode, parentNode)

  def childrenCanAAA(self):
    return self.psp.childrenCanAAA()
  def getAAALKernel(self):
    return TypedAAALKernel(self.psp.getAAALKernel(), self.f_type)

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

  # TODO Is this method part of the psp interface?
  def logDensityOfCounts(self,aux):
    return self.psp.logDensityOfCounts(aux)

class TypedAAALKernel(LKernel):
  def __init__(self, kernel, f_type):
    self.kernel = kernel
    self.f_type = f_type

  def simulate(self, trace, oldValue, args):
    return self.f_type.wrap_return(self.kernel.simulate(trace, self.f_type.unwrap_return(oldValue),
                                                        self.f_type.unwrap_args(args)))
  def weight(self, trace, newValue, oldValue, args):
    return self.kernel.weight(trace, self.f_type.unwrap_return(newValue),
                              self.f_type.unwrap_return(oldValue),
                              self.f_type.unwrap_args(args))

  def reverseWeight(self, trace, oldValue, args):
    return self.kernel.reverseWeight(trace,
                                     self.f_type.unwrap_return(oldValue),
                                     self.f_type.unwrap_args(args))
