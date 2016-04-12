import random

from venture.lite.env import VentureEnvironment
from venture.lite.utils import simulateCategorical

from venture.mite.sp import RequestReferenceSP
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

def simulateCRP(counts, alpha):
  return simulateCategorical(counts.values() + [alpha],
                             counts.keys() + [None])

def getNextTable(counts):
  while True:
    ret = random.getrandbits(30)
    if ret not in counts:
      return ret

class DPSP(RequestReferenceSP):
  def __init__(self, alpha, baseSpNode):
    super(DPSP, self).__init__()
    self.alpha = alpha
    self.baseSpNode = baseSpNode
    self.counts = {}

  def apply(self, args):
    raddr = simulateCRP(self.counts, self.alpha)
    if raddr is not None:
      args.incRequest(raddr)
    else:
      raddr = getNextTable(self.counts)
      exp = ["sp"]
      env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
      args.newRequest(raddr, exp, env)
      self.counts[raddr] = 0
    self.counts[raddr] += 1
    self.request_map[args.node] = raddr
    return args.requestedValue(raddr)

  def unapply(self, args):
    raddr = self.request_map.pop(args.node)
    self.counts[raddr] -= 1
    args.decRequest(raddr)

class DPMemSP(SimulationSP):
  def simulate(self, args):
    [_, baseSpNode] = args.operandNodes
    alpha = args.operandValue(0).getNumber()
    return DPSP(alpha, baseSpNode)

registerBuiltinSP("dpmem", DPMemSP())
