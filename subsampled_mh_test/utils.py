import math
import numpy as np
import numpy.random as npr
from venture.lite.builtin import deterministic_typed, naryNum, typed_nr
from venture.lite.psp import RandomPSP
from venture.lite.lkernel import LKernel
from venture.lite.utils import override
import venture.lite.value as v

def loadUtilSPs(ripl):
  utilSPsList = [
      [ "linear_logistic",
        deterministic_typed(lambda w,x: 1/(1+np.exp(-(w[0] + np.dot(w[1:], x)))),
        [v.ArrayUnboxedType(v.NumberType()), v.ArrayUnboxedType(v.NumberType())],
        v.NumberType(),
        descr="linear_logistic(w, x) returns the output of logistic regression with weight and input")],
      [ "line",
        naryNum(lambda x1, y1, x2, xnew: (xnew - x2) / float(x1 - x2) * y1,
        descr="line computes line prediction")],
      [ "multivariate_diag_normal", typed_nr(MVDNormalOutputPSP(),
          [v.ArrayUnboxedType(v.NumberType()), v.ArrayUnboxedType(v.NumberType())],
          v.ArrayUnboxedType(v.NumberType()))]]

  for name,sp in dict(utilSPsList).iteritems():
    ripl.bind_foreign_sp(name, sp)

class MVDNormalRandomWalkKernel(LKernel):
  def __init__(self,epsilon = 0.7):
    self.epsilon = epsilon if epsilon is not None else 0.7

  def simulate(self,trace,oldValue,args):
    (mu, _) = MVDNormalOutputPSP.__parse_args__(args)
    nu = npr.normal(0,self.epsilon,mu.shape)
    return oldValue + nu

  @override(LKernel)
  def weight(self, _trace, _newValue, _oldValue, _args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    return MVDNormalOutputPSP.logDensity(_newValue, _args)

class MVDNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    (mu, sigma) = self.__parse_args__(args)
    return mu + npr.normal(size = mu.shape) * sigma

  @staticmethod
  def logDensity(x, args):
    (mu, sigma) = MVDNormalOutputPSP.__parse_args__(args)
    return sum(-0.5 * ((x - mu) / sigma)**2 - 0.5 * np.log(2 * math.pi * sigma**2))

  def hasDeltaKernel(self): return True
  def getDeltaKernel(self,*args): return MVDNormalRandomWalkKernel(*args)

  def description(self,name):
    return "  (%s mean std) samples a vector according to the multivariate Gaussian distribution with a diagonal covariance matrix. It is an error if the vector arguments of mean and standard deviation do not have the same size." % name

  @staticmethod
  def __parse_args__(args):
    return (np.array(args.operandValues[0]), np.array(args.operandValues[1]))

