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
  typed_inf_sp2("resample", infer_action_type([v.IntegerType("particles : int")])),
  typed_inf_sp2("resample_serializing", infer_action_type([v.IntegerType("particles : int")])),
  typed_inf_sp2("resample_threaded", infer_action_type([v.IntegerType("particles : int")])),
  typed_inf_sp2("resample_thread_ser", infer_action_type([v.IntegerType("particles : int")])),
  typed_inf_sp2("resample_multiprocess", infer_action_type([v.IntegerType("particles : int"), v.IntegerType("max_processes : int")], min_req_args=1)),
  typed_inf_sp2("enumerative_diversify", infer_action_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")])),
  typed_inf_sp2("collapse_equal", infer_action_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")])),
  typed_inf_sp2("collapse_equal_map", infer_action_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")])),
  typed_inf_sp("draw_scaffold", transition_oper_type()),
  typed_inf_sp("subsampled_mh", transition_oper_type([v.IntegerType("Nbatch : int"), v.IntegerType("k0 : int"), v.NumberType("epsilon : number"),
                                                      v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")])),
  typed_inf_sp("mh_kernel_update", transition_oper_type([v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")])),
  typed_inf_sp("gibbs_update", par_transition_oper_type()),
  typed_inf_sp("pgibbs_update", par_transition_oper_type([v.IntegerType("particles : int")])),
  typed_inf_sp("subsampled_mh_check_applicability", transition_oper_type()),
  typed_inf_sp("subsampled_mh_make_consistent", transition_oper_type([v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")])),
  typed_inf_sp2("incorporate", infer_action_type([])),
  typed_inf_sp2("peek", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("plotf", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("plotf_to_file", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("printf", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("call_back", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("call_back_accum", infer_action_type([v.AnyType()], variadic=True)),
  typed_inf_sp2("assume", infer_action_type([v.AnyType("<symbol>"), v.AnyType("<expression>")])),
  typed_inf_sp2("observe", infer_action_type([v.AnyType("<expression>"), v.AnyType()])),
  typed_inf_sp2("predict", infer_action_type([v.AnyType("<expression>")])),
  typed_inf_sp2("load_plugin", infer_action_type([v.SymbolType("filename")])),

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
