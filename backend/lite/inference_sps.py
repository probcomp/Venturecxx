import sp
import psp

class MHOutputPSP(psp.DeterministicPSP):
  def simulate(self, args):
    return sp.VentureSP(psp.NullRequestPSP, psp.MadeMHOutputPSP(*args.operandValues))

class MadeMHOutputPSP(psp.RandomPSP):
  def __init__(self, scope, block, transitions):
    self.scope = scope
    self.block = block
    self.transitions = transitions
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].infer({"kernel":"mh","scope":self.scope,"block":self.block,"transitions":int(self.transitions),"with_mutation":True})
