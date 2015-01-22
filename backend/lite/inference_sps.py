import sp
import psp
import value as v
from builtin import no_request, deterministic_typed

class InferPrimitiveOutputPSP(psp.DeterministicPSP):
  def __init__(self, name, klass, desc, tp):
    self.name = name
    self.klass = klass
    self.desc = desc
    self.tp = tp
  def simulate(self, args):
    return sp.VentureSPRecord(sp.SP(psp.NullRequestPSP(),
                                    psp.TypedPSP(self.klass(self.name, args.operandValues), self.tp)))
  def description(self, _name):
    return self.desc

class MadeInferPrimitiveOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, exp):
    self.exp = [name] + exp
  def simulate(self, args):
    ans = args.operandValues[0].primitive_infer(self.exp)
    return (ans, args.operandValues[0])

class MadeEngineMethodInferOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, operands, desc=None):
    self.name = name
    self.operands = operands
    self.desc = desc
  def simulate(self, args):
    ans = getattr(args.operandValues[0], self.name)(*self.operands)
    return (ans, args.operandValues[0])
  def description(self, _name):
    return self.desc

def infer_action_type(return_type):
  return sp.SPType([v.ForeignBlobType()], v.PairType(return_type, v.ForeignBlobType()))

def infer_action_maker_type(args_types, return_type=None, **kwargs):
  # Represent the underlying trace as a ForeignBlob for now.
  if return_type is None:
    return_type = v.NilType()
  return sp.SPType(args_types, infer_action_type(return_type), **kwargs)

def typed_inf_sp(name, tp, klass, desc=""):
  return [ name, no_request(psp.TypedPSP(InferPrimitiveOutputPSP(name, klass=klass, desc=desc, tp=tp.return_type), tp)) ]

def trace_method_sp(name, tp, desc=""):
  return typed_inf_sp(name, tp, MadeInferPrimitiveOutputPSP, desc)

def engine_method_sp(name, tp, desc=""):
  return typed_inf_sp(name, tp, MadeEngineMethodInferOutputPSP, desc)

def transition_oper_args_types(extra_args = None):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  return [v.AnyType("scope : object"), v.AnyType("block : object")] + (extra_args if extra_args is not None else []) + [v.IntegerType("transitions : int")]

def transition_oper_type(extra_args = None, **kwargs):
  return infer_action_maker_type(transition_oper_args_types(extra_args), **kwargs)

def par_transition_oper_type(extra_args = None, **kwargs):
  other_args = transition_oper_args_types(extra_args)
  return infer_action_maker_type(other_args + [v.BoolType("in_parallel : bool")], min_req_args=len(other_args), **kwargs)

def macro_helper(name, tp):
  return engine_method_sp(name, tp, desc="""\
A helper function for implementing the eponymous inference macro.

Calling it directly is likely to be difficult and unproductive. """)

inferenceSPsList = [
  trace_method_sp("mh", transition_oper_type(), desc="""\
Run a Metropolis-Hastings kernel, proposing by resimulating the prior.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  trace_method_sp("func_mh", transition_oper_type(), desc="""\
Like mh, but functional.

To wit, represent the proposal with a new trace (sharing common
structure) instead of modifying the existing particle in place.

Up to log factors, there is no asymptotic difference between this and
`mh`, but the distinction is exposed for those who know what they are
doing."""),

  trace_method_sp("gibbs", par_transition_oper_type(), desc="""\
Run a Gibbs sampler that computes the local posterior by enumeration.

All the random choices identified by the scope-block pair must be
discrete.

The `transitions` argument specifies how many transitions of the
chain to run.

The `in-parallel` argument, if supplied, toggles parallel evaluation
of the local posterior.  Parallel evaluation is only available in the
Puma backend, and is on by default."""),

  trace_method_sp("emap", par_transition_oper_type(), desc="""\
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

  trace_method_sp("func_pgibbs",
                  par_transition_oper_type([v.IntegerType("particles : int")]),
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

  trace_method_sp("pgibbs",
                  par_transition_oper_type([v.IntegerType("particles : int")]),
                  desc="""\
Like ``func_pgibbs`` but reuse a single trace instead of having several.

The performance is asymptotically worse in the sequence length, but
does not rely on stochastic procedures being able to functionally
clone their auxiliary state.

The only reason to use this is if you know you want to. """),

  trace_method_sp("func_pmap",
                  par_transition_oper_type([v.IntegerType("particles : int")]),
                  desc="""\
Like func_pgibbs, but deterministically
select the maximum-likelihood particle at the end instead of sampling.

Iterated applications of func_pmap are guaranteed to grow in likelihood
(and therefore do not converge to the posterior)."""),

  trace_method_sp("meanfield",
                  transition_oper_type([v.IntegerType("training_steps : int")]),
                  desc="""\
Sample from a mean-field variational approximation of the local posterior.

The mean-field approximation is optimized with gradient ascent.  The
`training_steps` argument specifies how many steps to take.

The `transitions` argument specifies how many times to do this.

Note: There is currently no way to save the result of training the
variational approximation to be able to sample from it many times. """),

  trace_method_sp("print_scaffold_stats", transition_oper_type(), desc="""\
Print some statistics about the requested scaffold.

This may be useful as a diagnostic.

The `transitions` argument specifies how many times to do this;
this is not redundant if the `block` argument is ``one``."""),

  trace_method_sp("nesterov",
                  transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
                  desc="""\
Move deterministically toward the maximum of the local posterior by
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

  trace_method_sp("map",
                  transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
                  desc="""\
Move deterministically toward the maximum of the local posterior by
gradient ascent.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

This is just like ``nesterov``, except without the Nesterov
correction. """),

  trace_method_sp("hmc",
                  transition_oper_type([v.NumberType("step_size : number"), v.IntegerType("steps : int")]),
                  desc="""\
Run a Hamiltonian Monte Carlo transition kernel.

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

  trace_method_sp("rejection", transition_oper_type(min_req_args=2), desc="""\
Sample from the local posterior by rejection sampling.

Not available in the Puma backend.  Not all the builtin procedures
support all the density bound information necessary for this.

The `transitions` argument specifies how many times to do this.
Specifying more than 1 transition is redundant if the `block` is
anything other than ``one``. """),

  trace_method_sp("bogo_possibilize", transition_oper_type(min_req_args=2), desc="""\
Initialize the local inference problem to a possible state.

If the current local likelihood is 0, resimulate the local prior until
a non-zero likelihood state is found.

Notes:

- If the current state is possible, do nothing.

- This is different from rejection sampling because the distribution
  on results is not the posterior, but the prior conditioned on the
  likelihood being non-zero.  As such, it is likely to complete
  faster.

- This is different from likelihood weighting because a) it keeps
  trying automatically until it finds a possible state, and b) it does
  not modify the weight of the particle it is applied to (because if
  the scope and block are other than ``default all`` it is not clear
  what the weight should become).

The `transitions` argument specifies how many times to do this.
Specifying more than 1 transition is redundant if the `block` is
anything other than ``one``. """),

  trace_method_sp("slice",
                  transition_oper_type([v.NumberType("w : number"), v.IntegerType("m : int")]),
                  desc="""\
Slice sample from the local posterior of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the stepping-out procedure to find the slice.  The
`w` and `m` arguments parameterize the slice sampler in the standard
way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  trace_method_sp("slice_doubling",
                  transition_oper_type([v.NumberType("w : number"), v.IntegerType("p : int")]),
                  desc="""\
Slice sample from the local posterior of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the interval-doubling procedure to find the slice.
The `w` and `p` arguments parameterize the slice sampler in the
standard way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  engine_method_sp("resample",
                   infer_action_maker_type([v.IntegerType("particles : int")]),
                   desc="""\
Perform an SMC-style resampling step.

The `particles` argument gives the number of particles to make.
Subsequent modeling and inference commands will be applied to each
result particle independently.  Data reporting commands will talk to
one distinguished particle, except ``peek``.

Future observations will have the effect of weighting the particles
relative to each other by the relative likelihoods of observing those
values in those particles.  The resampling step respects those
weights.

The new particles will be handled in series.  See the next procedures
for alternatives."""),

  engine_method_sp("resample_multiprocess",
                   infer_action_maker_type([v.IntegerType("particles : int"), v.IntegerType("max_processes : int")], min_req_args=1),
                   desc="""\
Like ``resample``, but fork multiple OS processes to simulate the
resulting particles in parallel.

The `max_processes` argument, if supplied, puts a cap on the number of
processes to make.  The particles are distributed evenly among the
processes.  If no cap is given, fork one process per particle.

Subtlety: Collecting results (and especially performing further
resampling steps) requires inter-process communication, and therefore
requires serializing and deserializing any state that needs
transmitting.  ``resample_multiprocess`` is therefore not a drop-in
replacement for ``resample``, as the former will handle internal
states that cannot be serialized, whereas the latter will not.  """),

  engine_method_sp("resample_serializing",
                   infer_action_maker_type([v.IntegerType("particles : int")]),
                   desc="""\
Like ``resample``, but performs serialization the same way ``resample_multiprocess`` does.

Use this to debug serialization problems without messing with actually
spawning multiple processes.  """),

  engine_method_sp("resample_threaded",
                   infer_action_maker_type([v.IntegerType("particles : int")]),
                   desc="""\
Like ``resample_multiprocess`` but uses threads rather than actual processes, and does not serialize, transmitting objects in shared memory instead.

Python's global interpreter lock is likely to prevent any speed gains
this might have produced.

Might be useful for debugging concurrency problems without messing
with serialization and multiprocessing, but we expect such problems to
be rare. """),

  engine_method_sp("resample_thread_ser",
                   infer_action_maker_type([v.IntegerType("particles : int")]),
                   desc="""\
Like ``resample_threaded``, but serializes the same way ``resample_multiprocess`` does.

Python's global interpreter lock is likely to prevent any speed gains
this might have produced.

Might be useful for debugging concurrency+serialization problems
without messing with actual multiprocessing, but then one is messing
with multithreading."""),

  engine_method_sp("likelihood_weight", infer_action_maker_type([]), desc="""\
Likelihood-weight the full particle set.

Resample all particles in the current set from the prior and reset
their weights to the likelihood."""),

  engine_method_sp("enumerative_diversify",
                   infer_action_maker_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")]),
                   desc="""\
Diversify the current particle set to represent the local posterior exactly.

Specifically:

1) Compute the local posterior by enumeration of all possible values
   in the given scope and block

2) Fork every extant particle as many times are there are values

3) Give each new particle a relative weight proportional to the
   relative weight of its ancestor particle times the posterior
   probability of the chosen value.

Unlike most inference SPs, this transformation is deterministic.

This is useful together with ``collapse_equal`` and
``collapse_equal_map`` for implementing certain kinds of dynamic
programs in Venture. """),

  engine_method_sp("collapse_equal",
                   infer_action_maker_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")]),
                   desc="""\
Collapse the current particle set to represent the local posterior less redundantly.

Specifically:

1) Bin all extant particles by the (joint) values they exhibit on all
   random variables in the given scope and block (specify a block of
   "none" to have one bin)

2) Resample by relative weight within each bin, retaining one particle

3) Set the relative weight of the retained particle to the sum of the
   weights of the particles that formed the bin

Viewed as an operation on only the random variables in the given scope
and block, this is deterministic (the randomness only affects other
values).

This is useful together with ``enumerative_diversify`` for
implementing certain kinds of dynamic programs in Venture. """),

  engine_method_sp("collapse_equal_map",
                   infer_action_maker_type([v.ExpressionType("scope : object"), v.ExpressionType("block : object")]),
                   desc="""\
Like ``collapse_equal`` but deterministically retain the max-weight particle.

And leave its weight unaltered, instead of adding in the weights of
all the other particles in the bin. """),

  trace_method_sp("draw_scaffold", transition_oper_type(), desc="""\
Draw a visual representation of the scaffold indicated by the given scope and block.

This is useful for debugging.  You probably do not want to specify more than 1 transition."""),

  trace_method_sp("subsampled_mh",
                  transition_oper_type([v.IntegerType("Nbatch : int"), v.IntegerType("k0 : int"), v.NumberType("epsilon : number"),
                                        v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")]),
                  desc="""\
Run a subsampled Metropolis-Hastings kernel

per the Austerity MCMC paper.

Note: not all dependency structures that might occur in a scaffold are supported.  See ``subsampled_mh_check_applicability``.

Note: the resulting execution history may not actually be possible, so
may confuse other transition kernels.  See ``subsampled_mh_make_consistent``
and ``*_update``.  """),

  trace_method_sp("subsampled_mh_check_applicability", transition_oper_type(), desc="""\
Raise a warning if the given scope and block obviously do not admit subsampled MH

From the source::

   # Raise three types of warnings:
   # - SubsampledScaffoldNotEffectiveWarning: calling subsampled_mh will be the
   #   same as calling mh.
   # - SubsampledScaffoldNotApplicableWarning: calling subsampled_mh will cause
   #   incorrect behavior.
   # - SubsampledScaffoldStaleNodesWarning: stale node will affect the
   #   inference of other random variables. This is not a critical
   #   problem but requires one to call makeConsistent before other
   #   random nodes are selected as principal nodes.
   #
   # This method cannot check all potential problems caused by stale nodes.

"""),

  trace_method_sp("subsampled_mh_make_consistent",
                  transition_oper_type([v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")]),
                  desc="""\
Fix inconsistencies introduced by subsampled MH."""),

  trace_method_sp("mh_kernel_update",
                  transition_oper_type([v.BoolType("useDeltaKernels : bool"), v.NumberType("deltaKernelArgs : number"), v.BoolType("updateValues : bool")]),
                  desc="""\
Run a normal ``mh`` kernel, tolerating inconsistencies introduced by previous subsampled MH."""),

  trace_method_sp("gibbs_update", par_transition_oper_type(), desc="""\
Run a normal ``gibbs`` kernel, tolerating inconsistencies introduced by previous subsampled MH. """),

  trace_method_sp("pgibbs_update",
                  par_transition_oper_type([v.IntegerType("particles : int")]),
                  desc="""\
Run a normal ``pgibbs`` kernel, tolerating inconsistencies introduced by previous subsampled MH."""),

  engine_method_sp("incorporate", infer_action_maker_type([]), desc="""\
Make the history consistent with observations.

Specifically, modify the execution history so that the values of
variables that have been observed since the last ``incorporate`` match
the given observations.  If there are multiple particles, also adjust
their relative weights by the relative likelihoods of the
observations being incorporated.

This is done automatically at the beginning of every `infer` command,
but is also provided explicitly because it may be appropriate to
invoke in the middle of complex inference programs that introduce new
observations."""),

  engine_method_sp("likelihood_at",
                   infer_action_maker_type([v.AnyType("scope : object"), v.AnyType("block : object")], return_type=v.ArrayUnboxedType(v.NumberType())),
                   desc="""\
Compute and return the value of the local log likelihood at the given scope and block.

If there are stochastic nodes in the conditional regeneration graph,
returns a one-sample estimate of the local likelihood.

Compare posterior_at."""),

  engine_method_sp("posterior_at",
                   infer_action_maker_type([v.AnyType("scope : object"), v.AnyType("block : object")], return_type=v.ArrayUnboxedType(v.NumberType())),
                   desc="""\
Compute and return the value of the local log posterior at the given scope and block.

The principal nodes must be able to assess.  If there are stochastic
nodes in the conditional regeneration graph, returns a one-sample
estimate of the local posterior.

Compare likelihood_at."""),

  [ "particle_log_weights", no_request(psp.TypedPSP(MadeEngineMethodInferOutputPSP("particle_log_weights", [], desc="""\
Return the weights of all extant particles as an array of numbers (in log space).
"""), infer_action_type(v.ArrayUnboxedType(v.NumberType())))) ],

  engine_method_sp("set_particle_log_weights",
                   infer_action_maker_type([v.ArrayUnboxedType(v.NumberType())]),
                   desc="""\
Set the weights of the particles to the given array.  It is an error if the length of the array differs from the number of particles. """),

  engine_method_sp("load_plugin", infer_action_maker_type([v.SymbolType("filename")], variadic=True)),

  macro_helper("peek", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("plotf", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("plotf_to_file", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("printf", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("call_back", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("call_back_accum", infer_action_maker_type([v.AnyType()], variadic=True)),
  macro_helper("assume", infer_action_maker_type([v.AnyType("<symbol>"), v.AnyType("<expression>")])),
  macro_helper("observe", infer_action_maker_type([v.AnyType("<expression>"), v.AnyType()])),
  macro_helper("predict", infer_action_maker_type([v.AnyType("<expression>")])),
  macro_helper("sample", infer_action_maker_type([v.AnyType("<expression>")], return_type=v.AnyType())),
  macro_helper("sample_all", infer_action_maker_type([v.AnyType("<expression>")], return_type=v.ListType())),

  # Hackety hack hack backward compatibility
  ["ordered_range", deterministic_typed(lambda *args: (v.VentureSymbol("ordered_range"),) + args,
                                        [v.AnyType()], v.ListType(), variadic=True)]
]

inferenceKeywords = [ "default", "all", "none", "one", "ordered" ]
