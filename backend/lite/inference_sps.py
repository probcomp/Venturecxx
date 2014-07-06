import sp
import psp
import value as v
from builtin import typed_nr

class InferPrimitiveOutputPSP(psp.DeterministicPSP):
  def __init__(self, name):
    self.name = name
  def simulate(self, args):
    return sp.VentureSP(psp.NullRequestPSP(),
                        psp.TypedPSP(MadeInferPrimitiveOutputPSP(self.name, args.operandValues),
                                     sp.SPType([v.ForeignBlobType()], v.ForeignBlobType())))

class MadeInferPrimitiveOutputPSP(psp.RandomPSP):
  def __init__(self, name, exp):
    from venture.ripl.utils import expToDict
    self.params = expToDict([name] + exp)
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].infer(self.params)
    return args.operandValues[0]

def SPsListEntry(name, args_types):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  # Represent the underlying trace as a ForeignBlob for now.
  return [ name, typed_nr(InferPrimitiveOutputPSP(name), args_types,
                          sp.SPType([v.ForeignBlobType()], v.ForeignBlobType())) ],

inferenceSPsList = [
  SPsListEntry("mh", [v.ExpressionType(), v.ExpressionType(), v.IntegerType()])
]

inferenceKeywords = [ "default", "all", "one", "ordered" ]
