import random
import math
from utils import extendedLog, simulateCategorical, logDensityCategorical
from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, SPAux, VentureSPRecord, SPType
from lkernel import LKernel
from value import VentureAtom, BoolType # BoolType is metaprogrammed pylint:disable=no-name-in-module
from exception import VentureValueError

class DiscretePSP(RandomPSP):
  def logDensityBound(self, _x, _args): return 0

class BernoulliOutputPSP(DiscretePSP):
  def simulate(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    return random.random() < p
    
  def logDensity(self,val,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if val: return extendedLog(p)
    else: return extendedLog(1 - p)

  def gradientOfLogDensity(self, val, args):
    p = args.operandValues[0] if args.operandValues else 0.5
    deriv = 1/p if val else -1 / (1 - p)
    return (0, [deriv])

  def enumerateValues(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if p == 1: return [True]
    elif p == 0: return [False]
    else: return [True,False]

  def description(self,name):
    return "  (%s p) returns true with probability p and false otherwise.  If omitted, p is taken to be 0.5." % name

class CategoricalOutputPSP(DiscretePSP):
  # (categorical ps outputs)
  def simulate(self,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return simulateCategorical(args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      if not len(args.operandValues[0]) == len(args.operandValues[1]):
        raise VentureValueError("Categorical passed different length arguments.")
      return simulateCategorical(*args.operandValues)

  def logDensity(self,val,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return logDensityCategorical(val, args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      return logDensityCategorical(val,*args.operandValues)
  
  def enumerateValues(self,args):
    indexes = [i for i, p in enumerate(args.operandValues[0]) if p > 0]
    if len(args.operandValues) == 1: return indexes
    else: return [args.operandValues[1][i] for i in indexes]
  
  def description(self,name):
    return "  (%s weights objects) samples a categorical with the given weights.  In the one argument case, returns the index of the chosen option as an atom; in the two argument case returns the item at that index in the second argument.  It is an error if the two arguments have different length." % name

class UniformDiscreteOutputPSP(DiscretePSP):
  def simulate(self,args):
    if args.operandValues[1] <= args.operandValues[0]:
      raise VentureValueError("uniform_discrete called on invalid range (%d,%d)" % (args.operandValues[0],args.operandValues[1]))
    return random.randrange(*args.operandValues)

  def logDensity(self,val,args):
    a,b = args.operandValues
    if a <= val and val < b: return -math.log(b-a)
    else: return extendedLog(0.0)

  def enumerateValues(self,args): return range(*[int(x) for x in args.operandValues])

  def description(self,name):
    return "  (%s start end) samples a uniform discrete on the (start, start + 1, ..., end - 1)" % name

