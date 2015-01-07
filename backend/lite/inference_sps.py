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
  return [v.AnyType("scope : object"), v.AnyType("block : object")] + (extra_args if extra_args is not None else []) + [v.IntegerType("transitions : int")]

def transition_oper_type(extra_args = None, **kwargs):
  return infer_action_type(transition_oper_args_types(extra_args), **kwargs)

def par_transition_oper_type(extra_args = None, **kwargs):
  other_args = transition_oper_args_types(extra_args)
  return infer_action_type(other_args + [v.BoolType("in_parallel : bool")], min_req_args=len(other_args), **kwargs)

inferenceSPsList = [
  typed_inf_sp("mh", transition_oper_type(),
               desc="""Run a Metropolis-Hastings kernel, proposing by resimulating the prior.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  typed_inf_sp("func_mh", transition_oper_type(),
               desc="""Like mh, but functional.

To wit, represent the proposal with a new trace (sharing common
structure) instead of modifying the existing particle in place.

Up to log factors, there is no asymptotic difference between this and
`mh`, but the distinction is exposed for those who know what they are
doing."""),

  typed_inf_sp("latents", transition_oper_type()),

  typed_inf_sp("gibbs", par_transition_oper_type(),
               desc="""Run a Gibbs sampler that computes the local posterior by enumeration.

All the random choices identified by the scope-block pair must be
discrete.

The `transitions` argument specifies how many transitions of the
chain to run.

The `in-parallel` argument, if supplied, toggles parallel evaluation
of the local posterior.  Parallel evaluation is only available in the
Puma backend, and is on by default."""),

  typed_inf_sp("emap", par_transition_oper_type(),
               desc="""\
Deterministically move to the local posterior maximum (computed by
enumeration).

All the random choices identified by the scope-block pair must be
discrete.

The `transitions` argument specifies how many times to do this.
Specifying more than one transition is redundant unless the `block`
is ``one``.

The `in-parallel` argument, if supplied, toggles parallel evaluation
of the local posterior.  Parallel evaluation is only available in
the Puma backend, and is on by default."""),

  typed_inf_sp("func_pgibbs", par_transition_oper_type([v.IntegerType("particles : int")]),
               desc="""\
Move to a sample of the local posterior computed by particle Gibbs.

The `block` must indicate a sequential grouping of the random
choices in the `scope`.  This can be done by supplying the keyword
``ordered`` as the block, or the value of calling ``ordered_range``.

The `particles` argument specifies how many particles to use in the
particle Gibbs filter.

The `transitions` argument specifies how many times to do this.

The `in-parallel` argument, if supplied, toggles per-particle
parallelism.  Parallel evaluation is only available in the Puma
backend, and is on by default. """),

  typed_inf_sp("pgibbs", par_transition_oper_type([v.IntegerType("particles : int")]),
               desc="""\
Like ``func_pgibbs`` but reuse a single trace instead of having several.

The performance is asymptotically worse in the sequence length, but
does not rely on stochastic procedures being able to functionally
clone their auxiliary state.

The only reason to use this is if you know you want to. """),

  typed_inf_sp("func_pmap", par_transition_oper_type([v.IntegerType("particles : int")])),

  typed_inf_sp("meanfield", transition_oper_type([v.IntegerType("training_steps : int")]),
               desc="""Sample from a mean-field variational approximation of the local posterior.

The mean-field approximation is optimized with gradient ascent.  The
`training_steps` argument specifies how many steps to take.

The `transitions` argument specifies how many times to do this.

Note: There is currently no way to save the result of training the
variational approximation to be able to sample from it many times. """),

  typed_inf_sp("nesterov", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
               desc="""Move
deterministically toward the maximum of the local posterior by
Nesterov-accelerated gradient ascent.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

The gradient is of the log posterior.

The presence of discrete random choices in the scope-block pair will
not prevent this inference strategy, but none of the discrete
choices will be moved by the gradient steps.

The `step_size` argument gives how far to move along the gradient at
each point.

The `steps` argument gives how many steps to take.

The `transitions` argument specifies how many times to do this.

Note: the Nesterov acceleration is applied across steps within one
transition, not across transitions."""),

  typed_inf_sp("map", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
               desc="""Move
deterministically toward the maximum of the local posterior by
gradient ascent.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

This is just like ``nesterov``, except without the Nesterov
correction. """),

  typed_inf_sp("hmc", transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
               desc="""Run a Hamiltonian Monte Carlo transition kernel.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

The presence of discrete random choices in the scope-block pair will
not prevent this inference strategy, but none of the discrete
choices will be moved.

The `step_size` argument gives the step size of the integrator used
by HMC.

The `steps` argument gives how many steps to take in each HMC
trajectory.

The `transitions` argument specifies how many times to do this."""),

  typed_inf_sp("rejection", transition_oper_type(min_req_args=2),
               desc="""Sample from the local
posterior by rejection sampling.

Not available in the Puma backend.  Not all the builtin procedures
support all the density bound information necessary for this.

The `transitions` argument specifies how many times to do this.
Specifying more than 1 transition is redundant if the `block` is
anything other than ``one``. """),

  typed_inf_sp("slice", transition_oper_type([v.NumberType("w : number"), v.IntegerType("m : int")]),
               desc="""Slice sample from the local posterior of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the stepping-out procedure to find the slice.  The
`w` and `m` arguments parameterize the slice sampler in the standard
way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  typed_inf_sp("slice_doubling", transition_oper_type([v.NumberType("w : number"), v.IntegerType("p : int")]),
               desc="""Slice sample from the local posterior of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the interval-doubling procedure to find the slice.
The `w` and `p` arguments parameterize the slice sampler in the
standard way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  typed_inf_sp2("resample", infer_action_type([v.IntegerType("particles : int")]),
                desc="""Perform a resampling step.

The `particles` argument gives the number of particles to make.
Subsequent modeling and inference commands will be applied to each
result particle independently.  Data reporting commands will talk to
one distinguished particle, except ``peek_all``."""),

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

  typed_inf_sp2("incorporate", infer_action_type([]),
                desc="""Make the history consistent with observations.

This is done at the beginning of every `infer` command, but is also
provided explicitly because it may be appropriate to invoke in complex
inference programs that introduce new observations."""),

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
