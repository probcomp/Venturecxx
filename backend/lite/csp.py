from psp import DeterministicPSP, ESRRefOutputPSP
from sp import SP, VentureSPRecord
from env import VentureEnvironment
from request import Request,ESR
import value as v
from exception import VentureError

class CSPRequestPSP(DeterministicPSP):
  def __init__(self,ids,exp,addr,env):
    self.ids = ids
    self.exp = exp
    self.addr = addr
    self.env = env

  def simulate(self,args):
    if len(self.ids) != len(args.operandNodes):
      raise VentureError("Wrong number of arguments: compound takes exactly %d arguments, got %d." % (len(self.ids), len(args.operandNodes)))
    extendedEnv = VentureEnvironment(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,self.addr,extendedEnv)])

  def gradientOfSimulate(self, args, _value, _direction):
    # TODO Collect derivatives with respect to constants in the body
    # of the lambda and pass them through the constructor to whoever
    # came up with those constants.
    return [0 for _ in args.operandValues]

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class MakeCSPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    ids = args.operandValues[0]
    exp = args.operandValues[1]
    address = args.operandNodes[1].address
    return VentureSPRecord(SP(CSPRequestPSP(ids,exp,address,args.env),ESRRefOutputPSP()))

  def gradientOfSimulate(self, args, _value, _direction):
    # A lambda is a constant.  I may need to do some plumbing here,
    # depending on how I want to handle closed-over values.
    return [0 for _ in args.operandValues]

  def description(self,name):
    return "%s\n  Used internally in the implementation of compound procedures." % name
