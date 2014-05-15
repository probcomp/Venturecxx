from psp import DeterministicPSP, ESRRefOutputPSP
from sp import VentureSP
from env import VentureEnvironment
from request import Request,ESR
import value as v
import serialize

@serialize.register
class CSPRequestPSP(DeterministicPSP):
  def __init__(self,ids,exp,env):
    self.ids = ids
    self.exp = exp
    self.env = env

  def simulate(self,args):
    assert len(self.ids) == len(args.operandNodes)
    extendedEnv = VentureEnvironment(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,extendedEnv)])

  def gradientOfSimulate(self, args, _value, _direction):
    # TODO Collect derivatives with respect to constants in the body
    # of the lambda and pass them through the constructor to whoever
    # came up with those constants.
    return [0 for _ in args.operandValues]

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

  def serialize(self, s):
    ret = {}
    ret['ids'] = [s.serialize(id) for id in self.ids]
    ret['exp'] = s.serialize(self.exp)
    ret['env'] = s.serialize(self.env)
    return ret

  def deserialize(self, s, value):
    self.ids = [s.deserialize(id) for id in value['ids']]
    self.exp = s.deserialize(value['exp'])
    self.env = s.deserialize(value['env'])

class MakeCSPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    ids = args.operandValues[0]
    exp = args.operandValues[1]
    return VentureSP(CSPRequestPSP(ids,exp,args.env),ESRRefOutputPSP())

  def description(self,name):
    return "%s\n  Used internally in the implementation of compound procedures." % name
