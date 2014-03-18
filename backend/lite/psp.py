from abc import ABCMeta, abstractmethod
from lkernel import DefaultAAALKernel,DefaultVariationalLKernel,LKernel
from request import Request

class PSP(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,args): pass
  def gradientOfSimulate(self, _args, _value, _direction):
    """Should return the gradient of this psp's simulation function,
    with respect to the given direction on the output space, at the
    point given by the args struct (the input space is taken to be the
    full list of parents).  In other words, the Jacobian-vector
    product
      direction^T J_simulate(args).

    For SPs with one scalar output, the direction will be a number,
    and the correct answer is the gradient of simulate multiplied by
    that number.

    The value argument is the value that was output for these
    arguments, standing as a proxy for the randomness that this PSP
    had consumed to produce that value from the given args."""
    raise Exception("Cannot compute simulation gradient of %s", type(self))
  # These are good defaults for deterministic PSPs
  def logDensity(self, _value, _args): return 0
  def gradientOfLogDensity(self, _value, arg_list): return (0, [0 for _ in arg_list])
  def logDensityBound(self, _value, _args): return 0
  def incorporate(self,value,args): pass
  def unincorporate(self,value,args): pass
  # Returns a Python list of VentureValue objects
  def enumerateValues(self, _args): raise Exception("Cannot enumerate")
  def isRandom(self): return False
  def canAbsorb(self, _trace, _appNode, _parentNode): return False

  def childrenCanAAA(self): return False
  def getAAALKernel(self): return DefaultAAALKernel(self)

  def makesHSRs(self): return False
  def canEnumerate(self): return False

  def hasVariationalLKernel(self): return False
  def getVariationalLKernel(self,args): return DefaultVariationalLKernel(self, args)

  def hasSimulationKernel(self): return False
  def hasDeltaKernel(self): return False

  def description(self, _name): return None

  def madeSpLogDensityOfCountsBound(self, _aux):
    raise Exception("Cannot rejection sample AAA procedure with unbounded log density of counts")

class NullRequestPSP(PSP):
  def simulate(self,args): return Request()
  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class ESRRefOutputPSP(PSP):
  def simulate(self,args):
    assert len(args.esrNodes) ==  1
    return args.esrValues[0]

  def gradientOfSimulate(self, args, _value, direction):
    return [0 for _ in args.operandValues] + [direction]

  def canAbsorb(self,trace,appNode,parentNode):
    return parentNode != trace.esrParentsAt(appNode)[0] and parentNode != appNode.requestNode

class RandomPSP(PSP):
  __metaclass__ = ABCMeta
  @abstractmethod
  def simulate(self,args): pass
  def isRandom(self): return True
  def canAbsorb(self, _trace, _appNode, _parentNode): return True
  def logDensityBound(self, _value, _args):
    raise Exception("Cannot rejection sample psp %s %s with unbounded likelihood" % (type(self), self.description("psp")))

class TypedPSP(PSP):
  def __init__(self, psp, f_type):
    self.f_type = f_type
    self.psp = psp

  def simulate(self,args):
    return self.f_type.wrap_return(self.psp.simulate(self.f_type.unwrap_args(args)))
  def gradientOfSimulate(self, args, value, direction):
    return self.psp.gradientOfSimulate(self.f_type.unwrap_args(args), self.f_type.unwrap_return(value), direction)
  def logDensity(self,value,args):
    return self.psp.logDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def gradientOfLogDensity(self, value, args):
    # TODO maybe this should take an args object
    (dvalue, dargs) = self.psp.gradientOfLogDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_arg_list(args))
    return (self.f_type.wrap_return(dvalue), self.f_type.wrap_arg_list(dargs))
  def logDensityBound(self, value, args):
    return self.psp.logDensityBound(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
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
    return TypedLKernel(self.psp.getAAALKernel(), self.f_type)

  def makesHSRs(self): return self.psp.makeHSRs()
  def canEnumerate(self): return self.psp.canEnumerate()

  def hasVariationalLKernel(self): return self.psp.hasVariationalLKernel()
  def getVariationalLKernel(self,args):
    return TypedVariationalLKernel(self.psp.getVariationalLKernel(self.f_type.unwrap_args(args)), self.f_type)

  def hasSimulationKernel(self): return self.psp.hasSimulationKernel()
  def hasDeltaKernel(self): return self.psp.hasDeltaKernel()
  # TODO Wrap the simulation and delta kernels properly (once those are tested)

  def description(self,name):
    type_names = self.f_type.names()
    signature = "\n".join(["%s :: %s" % (name, variant) for variant in type_names])
    return signature + "\n" + self.psp.description(name)

  # TODO Is this method part of the psp interface?
  def logDensityOfCounts(self,aux):
    return self.psp.logDensityOfCounts(aux)

class TypedLKernel(LKernel):
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

  def weightBound(self, trace, newValue, oldValue, args):
    return self.kernel.weightBound(trace, self.f_type.unwrap_return(newValue),
                                   self.f_type.unwrap_return(oldValue),
                                   self.f_type.unwrap_args(args))

class TypedVariationalLKernel(TypedLKernel):
  def gradientOfLogDensity(self, value, args):
    return self.kernel.gradientOfLogDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def updateParameters(self, gradient, gain, stepSize):
    return self.kernel.updateParameters(gradient, gain, stepSize)
