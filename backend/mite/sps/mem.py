from venture.lite.env import VentureEnvironment

from venture.mite.sp import RequestReferenceSP
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class MemoizedSP(RequestReferenceSP):
  def __init__(self, spNode):
    super(MemoizedSP, self).__init__()
    self.spNode = spNode

  def request(self, args):
    operands = args.operandValues()
    raddr = tuple(operands)
    if args.hasRequest(raddr):
      args.incRequest(raddr)
    else:
      exp = ["sp"] + [["quote", operand] for operand in operands]
      env = VentureEnvironment(None, ["sp"], [self.spNode])
      args.newRequest(raddr, exp, env)
    return raddr

class MemSP(SimulationSP):
  def simulate(self, args):
    [spNode] = args.operandNodes
    return MemoizedSP(spNode)

registerBuiltinSP("mem", MemSP())
