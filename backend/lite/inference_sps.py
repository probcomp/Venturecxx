import sp
import psp
import value as v
from builtin import typed_nr, deterministic_typed

class InferPrimitiveOutputPSP(psp.DeterministicPSP):
  def __init__(self, name, klass):
    self.name = name
    self.klass = klass
  def simulate(self, args):
    return sp.VentureSPRecord(sp.SP(psp.NullRequestPSP(),
                                    psp.TypedPSP(self.klass(self.name, args.operandValues),
                                                 sp.SPType([v.ForeignBlobType()], v.ForeignBlobType()))))

class MadeInferPrimitiveOutputPSP(psp.RandomPSP):
  def __init__(self, name, exp):
    self.exp = [name] + exp
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    args.operandValues[0].primitive_infer(self.exp)
    return args.operandValues[0]

class MadeEngineMethodInferOutputPSP(psp.RandomPSP):
  def __init__(self, name, operands):
    self.name = name
    self.operands = operands
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    getattr(args.operandValues[0], self.name)(*self.operands)
    return args.operandValues[0]


def SPsListEntry(name, args_types, klass=MadeInferPrimitiveOutputPSP, **kwargs):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  # Represent the underlying trace as a ForeignBlob for now.
  return [ name, typed_nr(InferPrimitiveOutputPSP(name, klass=klass), args_types,
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
  SPsListEntry("slice", [v.ExpressionType(), v.ExpressionType(), v.NumberType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("slice_doubling", [v.ExpressionType(), v.ExpressionType(), v.NumberType(), v.IntegerType(), v.IntegerType()]),
  SPsListEntry("resample", [v.IntegerType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("draw_scaffold", [v.ExpressionType(), v.ExpressionType(), v.IntegerType()], min_req_args=3),
  # (subsampled_mh scope block Nbatch k0 epsilon useDeltaKernels deltaKernelArgs updateValues transitions)
  SPsListEntry("subsampled_mh", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.IntegerType(), v.NumberType(), v.BoolType(), v.NumberType(), v.BoolType(), v.IntegerType()], min_req_args=9),
  # (mh_kernel scope block useDeltaKernels deltaKernelArgs transitions)
  SPsListEntry("mh_kernel_update", [v.ExpressionType(), v.ExpressionType(), v.BoolType(), v.NumberType(), v.BoolType(), v.IntegerType()], min_req_args=6),
  SPsListEntry("gibbs_update", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.BoolType()], min_req_args=3),
  SPsListEntry("pgibbs_update", [v.ExpressionType(), v.ExpressionType(), v.IntegerType(), v.IntegerType(), v.BoolType()], min_req_args=4),
  # (subsampled_mh_check_applicability scope block transitions)
  SPsListEntry("subsampled_mh_check_applicability", [v.ExpressionType(), v.ExpressionType(), v.IntegerType()], min_req_args=3),
  # (subsampled_mh_make_consistent scope block useDeltaKernels deltaKernelArgs updateValues transitions)
  SPsListEntry("subsampled_mh_make_consistent", [v.ExpressionType(), v.ExpressionType(), v.BoolType(), v.NumberType(), v.BoolType(), v.IntegerType()], min_req_args=6),
  SPsListEntry("incorporate", [], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("peek", [v.AnyType(), v.SymbolType()], klass=MadeEngineMethodInferOutputPSP, min_req_args=1),
  SPsListEntry("peek_all", [v.AnyType(), v.SymbolType()], klass=MadeEngineMethodInferOutputPSP, min_req_args=1),
  SPsListEntry("plotf", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("printf", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),

  # Hackety hack hack backward compatibility
  ["ordered_range", deterministic_typed(lambda *args: (v.VentureSymbol("ordered_range"),) + args,
                                        [v.AnyType()], v.ListType(), variadic=True)]
]

inferenceKeywords = [ "default", "all", "one", "ordered" ]
