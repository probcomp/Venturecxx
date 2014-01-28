from psp import PSP
from request import Request,ESR
from env import Env
import numpy as np

### Simplex Points

class SimplexOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)

### Polymorphic Operators
class LookupOutputPSP(PSP):
  def simulate(self,args): 
    xs = args.operandValues[0]
    x = args.operandValues[1]
    if isinstance(xs,list) and isinstance(x,float): return xs[int(x)]
    else: return xs[x]

class ContainsOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[1] in args.operandValues[0]

class SizeOutputPSP(PSP):
  def simulate(self,args): return len(args.operandValues[0])

### Dicts
class DictOutputPSP(PSP):
  def simulate(self,args): 
    d = {}
    d.update(zip(*args.operandValues))
    return d

### Matrices
class MatrixOutputPSP(PSP):
  def simulate(self,args): return np.mat(args.operandValues[0])

### Arrays

class ArrayOutputPSP(PSP):
  def simulate(self,args): return np.array(args.operandValues)

class IsArrayOutputPSP(PSP):
  def simulate(self,args): return isinstance(args.operandValues[0],np.ndarray)


### Lists (use Python lists instead of VenturePairs
class PairOutputPSP(PSP):
  def simulate(self,args): return [args.operandValues[0]] + args.operandValues[1]

class IsPairOutputPSP(PSP): 
  def simulate(self,args): return len(args.operandValues[0]) > 0

class ListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues

class FirstListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues[0][0]

class SecondListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues[0][1]

class RestListOutputPSP(PSP): 
  def simulate(self,args): return args.operandValues[0][1:]

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
