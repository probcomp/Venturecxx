from psp import PSP
from request import Request,ESR
from env import Env
import numpy as np

### Simplex Points

class SimplexOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)
  def description(self,name):
    return "(%s <number0> ...) -> <simplex>" % name

### Polymorphic Operators
class LookupOutputPSP(PSP):
  def simulate(self,args): 
    xs = args.operandValues[0]
    x = args.operandValues[1]
    if isinstance(xs,list) and isinstance(x,float): return xs[int(x)]
    else: return xs[x]
  def description(self,name):
    return "(%s <collection k v> <object k>) -> <object v>" % name

class ContainsOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[1] in args.operandValues[0]
  def description(self,name):
    return "(%s <collection k v> <object k>) -> <bool>" % name

class SizeOutputPSP(PSP):
  def simulate(self,args): return len(args.operandValues[0])
  def description(self,name):
    return "(%s <collection k v>) -> <number>" % name

### Dicts
class DictOutputPSP(PSP):
  def simulate(self,args): 
    d = {}
    d.update(zip(*args.operandValues))
    return d
  def description(self,name):
    return "(%s <list k> <list v>) -> <collection k v>\n  Returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length." % name

### Matrices
class MatrixOutputPSP(PSP):
  def simulate(self,args): return np.mat(args.operandValues[0])
  def description(self,name):
    return "(%s <list <list <number>>>) -> <matrix>\n  The input is the list of rows of the matrix." % name

### Arrays

class ArrayOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)
  def description(self,name):
    return "(%s <object0> ...) -> <array>" % name

class IsArrayOutputPSP(PSP):
  def simulate(self,args): return isinstance(args.operandValues[0],np.ndarray)
  def description(self,name):
    return "(%s <object>) -> <bool>" % name

### Lists (use Python lists instead of VenturePairs
class PairOutputPSP(PSP):
  def simulate(self,args): return [args.operandValues[0]] + args.operandValues[1]
  def description(self,name):
    return "(%s <object> <list>) -> <list>" % name

class IsPairOutputPSP(PSP): 
  def simulate(self,args):
    return isinstance(args.operandValues[0],list) and len(args.operandValues[0]) > 0

  def description(self,name):
    return "(%s <object>) -> <bool>" % name

class ListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues
  def description(self,name):
    return "(%s <object0> ...) -> <list>" % name

class FirstListOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0][0]
  def description(self,name):
    return "(%s <list>) -> <object>" % name

class SecondListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues[0][1]
  def description(self,name):
    return "(%s <list>) -> <object>" % name

class RestListOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0][1:] # TODO Is this constant time in Python?
  def description(self,name):
    return "(%s <list>) -> <list>" % name

class MapListRequestPSP(PSP):
  def simulate(self,args):
    fNode = args.operandNodes[0]
    xs = args.operandValues[1]    

    request = Request()
    for i in range(len(xs)):
      x = xs[i]
      id = str([args.node] + [i])
      exp = ["mappedSP"] + [["quote",x]]
      env = Env(None,["mappedSP"],[fNode])
      request.esrs.append(ESR(id,exp,env))

    return request

class MapListOutputPSP(PSP):
  def simulate(self,args):
    return args.esrValues
  def description(self,name):
    return "(%s <SP a b> <list a>) -> <list b>" % name
