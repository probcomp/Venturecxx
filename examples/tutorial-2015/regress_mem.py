"""
Generalizing memoizer/emulator pattern.

Example:
  assume f = proc () { flip(0.7) };
  assume package = regress(f, make_beta_bernoulli, 1, 1);
  predict first(package)();
  predict first(package)();
  sample second(package);

  assume gpmem = proc (f, mean, cov) { regress_mem(f, make_gp, mean, cov) };
"""

from venture.lite.psp import DeterministicPSP, TypedPSP
from venture.lite.sp import SP, VentureSPRecord, SPType
from venture.lite.env import VentureEnvironment
from venture.lite.request import Request,ESR
from venture.lite.address import emptyAddress
from venture.lite.msp import MSPRequestPSP
from venture.lite.lkernel import SimulationAAALKernel
import venture.lite.value as vv

class RegressRequestPSP(DeterministicPSP):
  """
  Create f_emu by calling the maker with the given args.

  This class is based on CSPRequestPSP.
  """

  def simulate(self, args):
    emu_nodes = args.operandNodes[1:]
    ids = ["emu{0}".format(i) for i in range(len(emu_nodes))]
    exp = ids
    env = VentureEnvironment(None, ids, emu_nodes)
    return Request([ESR(args.node, exp, emptyAddress, env)])

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class RegressOutputPSP(DeterministicPSP):
  """
  Create f_probe, which wraps f, and return list(f_probe, f_emu).

  This class (except its simulate method) is based on DeterministicAAAMakerPSP.
  """

  def __init__(self, memoizing):
    if memoizing:
      self.requester_class = MSPRequestPSP
    else:
      self.requester_class = RegressComputeRequestPSP

  def simulate(self, args):
    f_node = args.operandNodes[0]

    # Extract f_emu's SPRecord (used to construct f_compute).
    assert len(args.esrNodes()) == 1
    f_emu_ground = args.trace.groundValueAt(args.esrNodes()[0])

    f_compute = VentureSPRecord(
      SP(self.requester_class(f_node),
         RegressComputeOutputPSP(f_emu_ground.sp.outputPSP)))
    f_compute.spAux = f_emu_ground.spAux

    # Return f_emu's SPRef (not the SPRecord), because if f_emu gets
    # resampled, the SPRecord becomes stale but the SPRef does
    # not. This prevents the "second package" bug where f_emu's
    # hypers fail to propagate after you take it out of the package.
    # (Normal AAA SPs don't have this problem because they turn into
    # SPRefs when they are made.)
    f_emu = args.esrValues()[0]
    return vv.pythonListToVentureList([f_compute, f_emu])

    # Note: it's still possible to expose a "first package" bug in
    # which f_compute goes stale if f_emu is some dynamic thing that
    # switches between different SP/aux types, but hopefully this
    # doesn't come up as much.

  def childrenCanAAA(self): return True
  def getAAALKernel(self): return RegressAAALKernel(self)

class RegressAAALKernel(SimulationAAALKernel):
  """
  This is based on DeterministicMakerAAALKernel.

  Actually, it doesn't do anything, but it needs to exist because
  RegressOutputPSP wants to act like an AAA procedure for dependency
  tracking.
  """

  def __init__(self,makerPSP): self.makerPSP = makerPSP
  def simulate(self, _trace, args):
    ## We aren't assuming that the output is an SPRecord.
    ## In fact, it should be a list of two SPRecords.
    ## And their auxs are already attached.
    # spRecord = self.makerPSP.simulate(args)
    # spRecord.spAux = args.madeSPAux
    # return spRecord

    ## So the new version is:
    return self.makerPSP.simulate(args)

  def weight(self, _trace, _newValue, _args):
    # The log density of counts should already have been paid for in
    # the request for f_emu, so we can just return 0.
    return 0

class RegressComputeRequestPSP(DeterministicPSP):
  """
  Non-memoizing SP wrapper.
  """

  def __init__(self,sharedOperatorNode):
    self.sharedOperatorNode = sharedOperatorNode

  def simulate(self,args):
    ids = ["operand{0}".format(i) for i in range(len(args.operandNodes))]
    exp = ["wrappedSP"] + ids
    env = VentureEnvironment(
      VentureEnvironment(None,["wrappedSP"],[self.sharedOperatorNode]),
      ids, args.operandNodes)
    return Request([ESR(args.node,exp,emptyAddress,env)])

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

# TODO Perhaps this could subclass ESRRefOutputPSP to correctly handle
# back-propagation?
class RegressComputeOutputPSP(DeterministicPSP):
  """
  Like ESRRefOutputPSP, but calls incorporate on the emu_psp.
  """

  def __init__(self,emu_psp):
    self.emu_psp = emu_psp

  def simulate(self,args):
    assert len(args.esrNodes()) == 1
    return args.esrValues()[0]

  def incorporate(self, value, args):
    self.emu_psp.incorporate(value, args)

  def unincorporate(self, value, args):
    self.emu_psp.unincorporate(value, args)

regress = SP(RegressRequestPSP(), RegressOutputPSP(False))
regress_mem = SP(RegressRequestPSP(), RegressOutputPSP(True))

def __venture_start__(ripl):
  ripl.bind_foreign_sp("regress", regress)
  ripl.bind_foreign_sp("regress_mem", regress_mem)
