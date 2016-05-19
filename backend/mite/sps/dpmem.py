import math
import random

from venture.lite.env import VentureEnvironment
from venture.lite.utils import simulateCategorical, logaddexp

from venture.mite.sp import RequestReferenceSP
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

def simulateCRP(counts, alpha, np_rng):
  return simulateCategorical(counts.values() + [alpha], np_rng,
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
    raddr = simulateCRP(self.counts, self.alpha, args.np_prng())
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
      if args.hasRequest(table) and args.requestedValue(table) == value:
        weights.append(count)
        tables.append(table)
    newTable = getNextTable(self.counts)
    exp = ["sp"]
    env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
    args.newRequest(newTable, exp, env)
    newWeight = args.constrain(newTable, value)
    weights.append(self.alpha * math.exp(newWeight))
    tables.append(newTable)

    numerator = math.log(sum(weights))
    denominator = math.log(self.alpha + sum(self.counts.values()))
    weight = numerator - denominator

    raddr = simulateCategorical(weights, args.np_prng(), tables)
    if raddr == newTable:
      self.counts[raddr] = 0
    else:
      args.decRequest(newTable)
      args.incRequest(raddr)
    self.counts[raddr] += 1
    self.request_map[args.node] = raddr

    return weight

  def unconstrain(self, args):
    from venture.mite.evaluator import EvalContext
    from copy import copy
    eargs = copy(args)
    eargs.context = EvalContext(args.trace)

    value = args.outputValue()
    raddr = self.request_map.pop(args.node)
    self.counts[raddr] -= 1
    if self.counts[raddr] == 0:
      newWeight = args.unconstrain(raddr)
    else:
      newTable = getNextTable(self.counts)
      exp = ["sp"]
      env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
      eargs.newRequest(newTable, exp, env)
      eargs.constrain(newTable, value)
      newWeight = args.unconstrain(newTable)
      eargs.decRequest(newTable)
    args.decRequest(raddr)
    args.setState(args.node, raddr, ext="constrained raddr")

    weights = []
    for table, count in self.counts.items():
      if args.hasRequest(table) and args.requestedValue(table) == value:
        weights.append(count)
    weights.append(self.alpha * math.exp(newWeight))

    numerator = math.log(sum(weights))
    denominator = math.log(self.alpha + sum(self.counts.values()))
    weight = numerator - denominator
    args.setState(args.node, weight, ext="constrained weight")

    return weight, self.apply(eargs)

  def reconstrain(self, value, args):
    raddr = self.request_map.pop(args.node)
    self.counts[raddr] -= 1
    args.decRequest(raddr)

    raddr = args.getState(args.node, ext="constrained raddr")
    if args.hasRequest(raddr):
      args.incRequest(raddr)
    else:
      exp = ["sp"]
      env = VentureEnvironment(None, ["sp"], [self.baseSpNode])
      args.newRequest(raddr, exp, env)
      args.constrain(raddr, value)
      self.counts[raddr] = 0
    self.counts[raddr] += 1
    self.request_map[args.node] = raddr
    assert value == args.requestedValue(raddr), (value, args.requestedValue(raddr))
    return args.getState(args.node, ext="constrained weight")

class DPMemSP(SimulationSP):
  def simulate(self, args):
    [_, baseSpNode] = args.operandNodes
    alpha = args.operandValue(0).getNumber()
    return DPSP(alpha, baseSpNode)

registerBuiltinSP("dpmem", DPMemSP())
