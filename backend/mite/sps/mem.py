from venture.lite.env import VentureEnvironment

from venture.mite.sp import RequestReferenceSP
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class MemoizedSP(RequestReferenceSP):
  def __init__(self, spNode):
    super(MemoizedSP, self).__init__()
    self.spNode = spNode
    self.memTable = {}

  def request(self, args):
    operands = tuple(args.operandValues())
    ref = self.memTable.get(operands)
    if ref is None:
      exp = ["sp"] + [["quote", operand] for operand in operands]
      env = VentureEnvironment(None, ["sp"], [self.spNode])
      ref = args.newRequest(exp, env)
      self.memTable[operands] = ref
    else:
      args.shareRequest(ref)
    return ref

class MemSP(SimulationSP):
  def simulate(self, args):
    [spNode] = args.operandNodes
    return MemoizedSP(spNode)

registerBuiltinSP("mem", MemSP())
