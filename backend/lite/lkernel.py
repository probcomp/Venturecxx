import copy
import numbers
from sp import VentureSPRecord
from value import VentureValue
import sys
import math

class LKernel(object):
  def simulate(self, _trace, _oldValue, _args):
    raise Exception("Simulate not implemented!")
  def weight(self, _trace, _newValue, _oldValue, _args): return 0
  def reverseWeight(self,trace,oldValue,args):
    return self.weight(trace,oldValue,None,args)
  def gradientOfReverseWeight(self, _trace, _value, args): return (0, [0 for _ in args.operandValues])
  def weightBound(self, _trace, _newValue, _oldValue, _args):
    # An upper bound on the value of weight over the variation
    # possible by changing the values of everything in the arguments
    # whose value is None.  Useful for rejection sampling.
    raise Exception("Cannot rejection sample with weight-unbounded LKernel of type %s" % type(self))

class DefaultAAALKernel(LKernel):
  def __init__(self,makerPSP): self.makerPSP = makerPSP
  def simulate(self,_trace,_oldValue,args):
    spRecord = self.makerPSP.simulate(args)
    spRecord.spAux = args.madeSPAux
    return spRecord
  def weight(self,_trace,newValue,_oldValue,args):
    assert isinstance(newValue,VentureSPRecord)
    return newValue.sp.outputPSP.logDensityOfCounts(newValue.spAux)
  def weightBound(self, _trace, _newValue, _oldValue, args):
    # Going through the maker here because the new value is liable to
    # be None when computing bounds for rejection, but the maker
    # should know enough about its possible values future to answer my
    # question.
    return self.makerPSP.madeSpLogDensityOfCountsBound(newValue.spAux)

class DeterministicLKernel(LKernel):
  def __init__(self,psp,value):
    self.psp = psp
    self.value = value
    assert isinstance(value, VentureValue)

  def simulate(self,_trace,_oldValue,_args): return self.value
  def weight(self, _trace, newValue, _oldValue, args):
    answer = self.psp.logDensity(newValue,args)
    assert isinstance(answer, numbers.Number)
    return answer
  def gradientOfReverseWeight(self, _trace, newValue, args):
    return self.psp.gradientOfLogDensity(newValue, args)

######## Variational #########

class VariationalLKernel(LKernel):
  def gradientOfLogDensity(self, _value, _args): return 0
  def updateParameters(self,gradient,gain,stepSize): pass

class DefaultVariationalLKernel(VariationalLKernel):
  def __init__(self,psp,args):
    self.psp = psp
    self.parameters = args.operandValues
    self.parameterScopes = psp.getParameterScopes()

  def simulate(self,_trace,_oldValue,_args):
    return self.psp.simulateNumeric(self.parameters)

  def weight(self, _trace, newValue, _oldValue, args):
    ld = self.psp.logDensityNumeric(newValue,args.operandValues)
    proposalLD = self.psp.logDensityNumeric(newValue,self.parameters)
    w = ld - proposalLD
    assert not math.isinf(w) and not math.isnan(w)
    return w

  def gradientOfLogDensity(self, value, args):
    new_args = copy.copy(args)
    new_args.operandValues = self.parameters
    # Ignore the derivative of the value because we do not care about it
    (_, grad) = self.psp.gradientOfLogDensity(value, new_args)
    return grad

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
