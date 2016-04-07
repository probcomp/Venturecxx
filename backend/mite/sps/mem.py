from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError

from venture.mite.sp import RequestReferenceSP
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

# mem re-entrancy sentinel, guaranteed to be a unique object
# used to indicate that a mem table entry is now being computed.

sentinel = object()

class MemoizedSP(RequestReferenceSP):
  def __init__(self, spNode):
    super(MemoizedSP, self).__init__()
    self.spNode = spNode
    self.memTable = {}

  def request(self, args):
    operands = tuple(args.operandValues())
    ref = self.memTable.get(operands)
    if ref is None:
      self.memTable[operands] = sentinel
      try:
        exp = ["sp"] + [["quote", operand] for operand in operands]
        env = VentureEnvironment(None, ["sp"], [self.spNode])
        ref = args.newRequest(exp, env)
      finally:
        # Remove the sentinel, even if the evaluation threw an error.
        assert self.memTable[operands] is sentinel
        del self.memTable[operands]
      self.memTable[operands] = ref
    elif ref is sentinel:
      # This can only happen if a recursive memoized function
      # called itself with the same arguments.
      raise VentureError("Recursive mem argument loop detected.")
    else:
      args.shareRequest(ref)
    return ref

class MemSP(SimulationSP):
  def simulate(self, args):
    [spNode] = args.operandNodes
    return MemoizedSP(spNode)

registerBuiltinSP("mem", MemSP())
