from psp import PSP
from request import Request,ESR
from env import VentureEnvironment
import value as v

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
    for (i,x) in enumerate(xs):
      id = str([args.node] + [i])
      exp = ["mappedSP", ["quote",x]]
      env = VentureEnvironment(None,["mappedSP"],[fNode])
      request.esrs.append(ESR(id,exp,env))

    return request

class MapListOutputPSP(PSP):
  def simulate(self,args):
    return v.pythonListToVentureList(*args.esrValues)
  def description(self,name):
    return "(%s <SP a b> <list a>) -> <list b>" % name
