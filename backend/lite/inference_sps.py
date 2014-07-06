import sp
import psp
import value as v
from builtin import typed_nr, deterministic_typed

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
    if "in_parallel" not in self.params:
      self.params['in_parallel'] = True
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].infer(self.params)
    return args.operandValues[0]

def SPsListEntry(name, args_types, **kwargs):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  # Represent the underlying trace as a ForeignBlob for now.
  return [ name, typed_nr(InferPrimitiveOutputPSP(name), args_types,
                          sp.SPType([v.ForeignBlobType()], v.ForeignBlobType()),
                          **kwargs) ]

def basicInfer(name):
  return SPsListEntry(name, [v.ExpressionType(), v.ExpressionType(), v.IntegerType()])

inferenceSPsList = [basicInfer(n) for n in ["mh", "func_mh", "slice", "latents"]] + [
  SPsListEntry("gibbs", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.BoolType()], min_req_args=3),
  SPsListEntry("emap", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.BoolType()], min_req_args=3),
  SPsListEntry("pgibbs", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.IntegerType(), v.BoolType()], min_req_args=4),
  SPsListEntry("func_pgibbs", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.IntegerType(), v.BoolType()], min_req_args=4),
  SPsListEntry("meanfield", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("hmc", [v.ExpressionType(), v.ExpressionType(), v.NumberType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("map", [v.ExpressionType(), v.ExpressionType(), v.NumberType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("nesterov", [v.ExpressionType(), v.ExpressionType(), v.NumberType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("rejection", [v.ExpressionType(), v.ExpressionType(), v.IntegerType()], min_req_args=2),
  SPsListEntry("resample", [v.IntegerType()]),
  SPsListEntry("incorporate", []),

  # TODO Cycle, mixture, loop, peek, plotf

  # Hackety hack hack backward compatibility
  ["ordered_range", deterministic_typed(lambda *args: [v.VentureSymbol("ordered_range")] + args,
                                        [v.AnyType()], v.ListType(), variadic=True)]
]

inferenceKeywords = [ "default", "all", "one", "ordered" ]
