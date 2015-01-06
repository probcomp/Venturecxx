import sp
import psp
import value as v
from builtin import no_request, deterministic_typed

class InferPrimitiveOutputPSP(psp.DeterministicPSP):
  def __init__(self, name, klass, desc):
    self.name = name
    self.klass = klass
    self.desc = desc
  def simulate(self, args):
    return sp.VentureSPRecord(sp.SP(psp.NullRequestPSP(),
                                    psp.TypedPSP(self.klass(self.name, args.operandValues),
                                                 sp.SPType([v.ForeignBlobType()], v.ForeignBlobType()))))
  def description(self, _name):
    return self.desc

class MadeInferPrimitiveOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, exp):
    self.exp = [name] + exp
  def simulate(self, args):
    args.operandValues[0].primitive_infer(self.exp)
    return args.operandValues[0]

class MadeEngineMethodInferOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, operands):
    self.name = name
    self.operands = operands
  def simulate(self, args):
    getattr(args.operandValues[0], self.name)(*self.operands)
    return args.operandValues[0]

def infer_action_type(args_types, **kwargs):
  # Represent the underlying trace as a ForeignBlob for now.
  return sp.SPType(args_types, sp.SPType([v.ForeignBlobType()], v.ForeignBlobType()), **kwargs)

def typed_inf_sp(name, tp, klass=MadeInferPrimitiveOutputPSP, desc=""):
  return [ name, no_request(psp.TypedPSP(InferPrimitiveOutputPSP(name, klass=klass, desc=desc), tp)) ]

def typed_inf_sp2(name, tp, klass=MadeEngineMethodInferOutputPSP, desc=""):
  return typed_inf_sp(name, tp, klass, desc)

def SPsListEntry(name, args_types, klass=MadeInferPrimitiveOutputPSP, desc="", **kwargs):
  return typed_inf_sp(name, infer_action_type(args_types, **kwargs), klass=klass, desc=desc)

def transition_oper_args_types(extra_args = None):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  return [v.ExpressionType("scope : object"), v.ExpressionType("block : object")] + (extra_args if extra_args is not None else []) + [v.IntegerType("transitions : int")]

def transition_oper_type(extra_args = None, **kwargs):
  return infer_action_type(transition_oper_args_types(extra_args), **kwargs)

def par_transition_oper_type(extra_args = None, **kwargs):
  other_args = transition_oper_args_types(extra_args)
  return infer_action_type(other_args + [v.BoolType("in_parallel : bool")], min_req_args=len(other_args), **kwargs)

inferenceSPsList = [
  typed_inf_sp("mh", transition_oper_type()),
  typed_inf_sp("func_mh", transition_oper_type()),
  typed_inf_sp("latents", transition_oper_type()),
  typed_inf_sp("gibbs", par_transition_oper_type()),
  typed_inf_sp("emap", par_transition_oper_type()),
  typed_inf_sp("pgibbs", par_transition_oper_type([v.IntegerType("particles : int")])),
  typed_inf_sp("func_pgibbs", par_transition_oper_type([v.IntegerType("particles : int")])),
  typed_inf_sp("func_pmap", par_transition_oper_type([v.IntegerType("particles : int")])),
  typed_inf_sp("meanfield", transition_oper_type([v.IntegerType("steps : int")])),
  typed_inf_sp("hmc", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")])),
  typed_inf_sp("map", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")])),
  typed_inf_sp("nesterov", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")])),
  typed_inf_sp("rejection", transition_oper_type(min_req_args=2)),
  typed_inf_sp("slice", transition_oper_type([v.NumberType("w : number"), v.IntegerType("m : int")])),
  typed_inf_sp("slice_doubling", transition_oper_type([v.NumberType("w : number"), v.IntegerType("p : int")])),
  SPsListEntry("resample", [v.IntegerType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("resample_serializing", [v.IntegerType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("resample_threaded", [v.IntegerType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("resample_thread_ser", [v.IntegerType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("resample_multiprocess", [v.IntegerType(), v.IntegerType()], klass=MadeEngineMethodInferOutputPSP, min_req_args=1),
  SPsListEntry("enumerative_diversify", [v.ExpressionType(), v.ExpressionType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("collapse_equal", [v.ExpressionType(), v.ExpressionType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("collapse_equal_map", [v.ExpressionType(), v.ExpressionType()], klass=MadeEngineMethodInferOutputPSP),
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
  SPsListEntry("peek", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("plotf", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("plotf_to_file", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("printf", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("call_back", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("call_back_accum", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP, variadic=True),
  SPsListEntry("assume", [v.AnyType(), v.AnyType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("observe", [v.AnyType(), v.AnyType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("predict", [v.AnyType()], klass=MadeEngineMethodInferOutputPSP),
  SPsListEntry("load_plugin", [v.SymbolType()], klass=MadeEngineMethodInferOutputPSP),

  # Hackety hack hack backward compatibility
  ["ordered_range", deterministic_typed(lambda *args: (v.VentureSymbol("ordered_range"),) + args,
                                        [v.AnyType()], v.ListType(), variadic=True)]
]

inferenceKeywords = [ "default", "all", "none", "one", "ordered" ]

# Documentation of call_back (for lack of any better place to put it):

# (call_back <symbol> <expression>...)    Inference special form
#   Invokes the Python function registered under the name <symbol>
#   (see bind_callback) with
#   - First, the Infer instance in which the present inference program
#     is being run
#   - Then, for each expression in the call_back form, a list of
#     values for that expression, represented as stack dicts, sampled
#     across all extant particles.  The lists are parallel to each
#     other.
#
# ripl.bind_callback(<name>, <callable>)  RIPL method
#   Bind the given callable as a callback function that can be
#   referred to by "call_back" by the given name (which is a string).

# There is an example in test/inference_language/test_callback.py
