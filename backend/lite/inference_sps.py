import sp
import psp
import value as v
from builtin import typed_nr

class MHOutputPSP(psp.DeterministicPSP):
  def simulate(self, args):
    return sp.VentureSP(psp.NullRequestPSP, MadeMHOutputPSP(*args.operandValues))

class MadeMHOutputPSP(psp.RandomPSP):
  def __init__(self, scope, block, transitions):
    self.scope = scope
    self.block = block
    self.transitions = transitions
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].infer({"kernel":"mh","scope":self.scope,"block":self.block,"transitions":int(self.transitions),"with_mutation":True})
    return args.operandValues[0]

inferenceSPsList = [
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  # Represent the underlying trace as a ForeignBlob for now.
  [ "mh", typed_nr(MHOutputPSP(),
                   [v.ExpressionType(), v.ExpressionType(), v.IntegerType()],
                   sp.SPType([v.ForeignBlobType()], v.ForeignBlobType())) ],
]

inferenceKeywords = [ "default", "all", "one", "ordered" ]
