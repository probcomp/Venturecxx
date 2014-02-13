from psp import PSP
from request import Request,ESR
from env import VentureEnvironment
import numpy as np
import value as v

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
    keys = args.operandValues[0].asPythonList()
    vals = args.operandValues[1].asPythonList()
    return v.VentureDict(dict(zip(keys, vals)))
  def description(self,name):
    return "(%s <list k> <list v>) -> <collection k v>\n  Returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length." % name

### Map, the weird way.
class MapListRequestPSP(PSP):
  def simulate(self,args):
    fNode = args.operandNodes[0]
    xs = args.operandValues[1].asPythonList()

    request = Request()
    for i in range(len(xs)):
      x = xs[i]
      id = str([args.node] + [i])
      exp = ["mappedSP"] + [["quote",x]]
      env = VentureEnvironment(None,["mappedSP"],[fNode])
      request.esrs.append(ESR(id,exp,env))

    return request

class MapListOutputPSP(PSP):
  def simulate(self,args):
    return v.pythonListToVentureList(*args.esrValues)
  def description(self,name):
    return "(%s <SP a b> <list a>) -> <list b>" % name
