import math
import random

from venture.lite.env import VentureEnvironment
from venture.lite.utils import simulateCategorical, logaddexp

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
    args.setState(args.node, raddr)

  def restore(self, args):
    raddr = args.getState(args.node)
    if args.hasRequest(raddr):
      args.incRequest(raddr)
    else:
      exp = ["sp"]
      env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
      args.newRequest(raddr, exp, env)
      self.counts[raddr] = 0
    self.counts[raddr] += 1
    self.request_map[args.node] = raddr
    return args.requestedValue(raddr)

  def constrain(self, value, args):
    raddr = self.request_map.pop(args.node)
    self.counts[raddr] -= 1
    args.decRequest(raddr)

    weights = []
    tables = []
    for table, count in self.counts.items():
      if args.hasRequest(raddr) and args.requestedValue(table) == value:
        weights.append(count)
        tables.append(table)
    newTable = getNextTable(self.counts)
    exp = ["sp"]
    env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
    args.newRequest(newTable, exp, env)
    newWeight = args.constrain(newTable, value)
    weights.append(self.alpha * math.exp(newWeight))
    tables.append(newTable)

    raddr = simulateCategorical(weights, tables)
    if raddr == newTable:
      self.counts[raddr] = 0
    else:
      args.decRequest(newTable)
      args.incRequest(raddr)
    self.counts[raddr] += 1
    self.request_map[args.node] = raddr

    return logaddexp(weights) - math.log(self.alpha + len(self.counts))

  def unconstrain(self, args):
    value = args.outputValue()
    raddr = self.request_map.pop(args.node)
    self.counts[raddr] -= 1
    if self.counts[raddr] == 0:
      newWeight = args.unconstrain(raddr)
    else:
      newTable = getNextTable(self.counts)
      exp = ["sp"]
      env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
      args.newRequest(newTable, exp, env)
      args.constrain(newTable, value)
      newWeight = args.unconstrain(newTable)
      args.decRequest(newTable)
    args.decRequest(raddr)

    weights = []
    for table, count in self.counts.items():
      if args.hasRequest(raddr) and args.requestedValue(table) == value:
        weights.append(count)
    weights.append(newWeight)
    weight = logaddexp(weights) - math.log(self.alpha + len(self.counts))

    return weight, self.apply(args)

class DPMemSP(SimulationSP):
  def simulate(self, args):
    [_, baseSpNode] = args.operandNodes
    alpha = args.operandValue(0).getNumber()
    return DPSP(alpha, baseSpNode)

registerBuiltinSP("dpmem", DPMemSP())
