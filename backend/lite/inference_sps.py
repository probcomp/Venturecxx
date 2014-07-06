import sp
import psp
import value as v
from builtin import typed_nr

class MHOutputPSP(psp.DeterministicPSP):
  def simulate(self, args):
    return sp.VentureSP(psp.NullRequestPSP(),
                        psp.TypedPSP(MadeMHOutputPSP(args.operandValues),
                                     sp.SPType([v.ForeignBlobType()], v.ForeignBlobType())))

class MadeMHOutputPSP(psp.RandomPSP):
  def __init__(self, exp):
    from venture.ripl.utils import expToDict
    self.params = expToDict(["mh"] + exp)
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].infer(self.params)
    return args.operandValues[0]

inferenceSPsList = [
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  # Represent the underlying trace as a ForeignBlob for now.
  [ "mh", typed_nr(MHOutputPSP(),
                   [v.ExpressionType(), v.ExpressionType(), v.IntegerType()],
                   sp.SPType([v.ForeignBlobType()], v.ForeignBlobType())) ],
]

inferenceKeywords = [ "default", "all", "one", "ordered" ]
