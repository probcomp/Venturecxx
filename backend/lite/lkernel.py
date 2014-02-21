from abc import ABCMeta, abstractmethod
from sp import VentureSP
from value import VentureValue
import sys
import math

class LKernel(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,trace,oldValue,args): pass
  def weight(self,trace,newValue,oldValue,args): return 0
  def reverseWeight(self,trace,oldValue,args):
    return self.weight(trace,oldValue,None,args)

class DefaultAAALKernel(LKernel):
  def __init__(self,makerPSP): self.makerPSP = makerPSP
  def simulate(self,trace,oldValue,args): return self.makerPSP.simulate(args)
  def weight(self,trace,newValue,oldValue,args):
    assert isinstance(newValue,VentureSP)
    return newValue.outputPSP.logDensityOfCounts(args.madeSPAux)

class DeterministicLKernel(LKernel):
  def __init__(self,sp,value):
    self.sp = sp
    self.value = value
    assert isinstance(value, VentureValue)

  def simulate(self,trace,oldValue,args): return self.value
  def weight(self,trace,newValue,oldValue,args): return self.sp.logDensity(newValue,args)

######## Variational #########

class VariationalLKernel(LKernel):
  def gradientOfLogDensity(self,value,args): return 0
  def updateParameters(self,gradient,gain,stepSize): pass

class DefaultVariationalLKernel(VariationalLKernel):
  def __init__(self,psp,args):
    self.psp = psp
    self.parameters = args.operandValues
    self.parameterScopes = psp.getParameterScopes()

  def simulate(self,trace,oldValue,args):
    return self.psp.simulateNumeric(self.parameters)

  def weight(self,trace,newValue,oldValue,args): 
    ld = self.psp.logDensityNumeric(newValue,args.operandValues)
    proposalLD = self.psp.logDensityNumeric(newValue,self.parameters)
    w = ld - proposalLD
    assert not math.isinf(w) and not math.isnan(w)
    return w
    
  def gradientOfLogDensity(self,value,args):
    return self.psp.gradientOfLogDensity(value, self.parameters)

  def updateParameters(self,gradient,gain,stepSize):
    # TODO hacky numerical stuff
    minFloat = -sys.float_info.max
    maxFloat = sys.float_info.max
    for i in range(len(self.parameters)):
      self.parameters[i] += gradient[i] * gain * stepSize
      if self.parameters[i] < minFloat: self.parameters[i] = minFloat
      if self.parameters[i] > maxFloat: self.parameters[i] = maxFloat
      if self.parameterScopes[i] == "POSITIVE_REAL" and \
         self.parameters[i] < 0.1: self.parameters[i] = 0.1
      assert not math.isinf(self.parameters[i]) and not math.isnan(self.parameters[i])
