from psp import PSP
from request import Request,ESR
from env import Env
import numpy as np

### Simplex Points

class SimplexOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)
  def description(self,name): return "(simplex <arg0> ...) -> <simplex>"

### Polymorphic Operators
class LookupOutputPSP(PSP):
  def simulate(self,args): 
    xs = args.operandValues[0]
    x = args.operandValues[1]
    if isinstance(xs,list) and isinstance(x,float): return xs[int(x)]
    else: return xs[x]
  def description(self,name):
    return "(lookup <collection> <key>) -> <object>"

class ContainsOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[1] in args.operandValues[0]
  def description(self,name):
    return "(contains <collection> <key>) -> <bool>"

class SizeOutputPSP(PSP):
  def simulate(self,args): return len(args.operandValues[0])
  def description(self,name):
    return "(size <collection>) -> <number>"

### Dicts
class DictOutputPSP(PSP):
  def simulate(self,args): 
    d = {}
    d.update(zip(*args.operandValues))
    return d
  def description(self,name):
    return "dict :: [k] -> [v] -> Dict k v"

### Matrices
class MatrixOutputPSP(PSP):
  def simulate(self,args): return np.mat(args.operandValues[0])
  def description(self,name):
    return "matrix :: [[Number]] -> Matrix"

### Arrays

class ArrayOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)
  def description(self,name):
    return "(array <arg0> ...) -> <array>"

class IsArrayOutputPSP(PSP):
  def simulate(self,args): return isinstance(args.operandValues[0],np.ndarray)
  def description(self,name):
    return "(is_array <object>) -> <bool>"

### Lists (use Python lists instead of VenturePairs
class PairOutputPSP(PSP):
  def simulate(self,args): return [args.operandValues[0]] + args.operandValues[1]
  def description(self,name):
    return "pair :: a -> [a] -> [a]"

class IsPairOutputPSP(PSP): 
  def simulate(self,args): return len(args.operandValues[0]) > 0
  def description(self,name):
    return "(is_pair <object>) -> <bool>"

class ListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues
  def description(self,name):
    return "(list <arg0> ...) -> <list>"

class FirstListOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0][0]
  def description(self,args):
    return "(first <list>) -> <object>"

class SecondListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues[0][1]
  def description(self,args):
    return "(second <list>) -> <object>"

class RestListOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0][1:]
  def description(self,args):
    return "(rest <list>) -> <list>"

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
  def description(self,args):
    return "map_list :: (a -> b) -> [a] -> [b]"
