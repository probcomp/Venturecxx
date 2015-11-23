# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import sp
import psp
import value as v
import types as t
from sp_help import no_request, deterministic_typed
from exception import VentureError, VentureTypeError
from venture.engine.inference import Dataset
from venture.exception import VentureException
from venture.lite.value import VentureForeignBlob
from venture.lite.exception import VentureValueError
from venture.engine.plot_spec import PlotSpec
from venture.lite.records import VentureRecord, RecordType

class InferPrimitiveOutputPSP(psp.DeterministicPSP):
  def __init__(self, val, klass, desc, tp):
    self.val = val
    self.klass = klass
    self.desc = desc
    self.tp = tp
  def simulate(self, args):
    result = self.klass(self.val, args.operandValues())
    if self.klass is MadeRiplMethodInferOutputPSP:
      # Hack to allow MadeRiplMethodInferOutputPSP s to blame the
      # maker application for errors.
      result.addr = args.node.address
    result_sp = sp.VentureSPRecord(sp.SP(psp.NullRequestPSP(),
                                         psp.TypedPSP(result, self.tp.field_type)))
    # See note below
    return VentureRecord("inference_action", [result_sp])
  def description(self, _name):
    return self.desc

# Note on returning VentureRecord from InferPrimitiveOutputPSP.

# Returning an SP inside a structure currently doesn't play very well
# with PETs, because it fools the detection of constructed
# VentureSPRecords and the allocation of SPRefs for them.  The effect
# here is that tracing one of these inference actions in the Lite
# backend may produce strange effects.
#
# Options:
# - Don't wrap these primitives in inference action records, and
#   instead define compounds in the inference prelude that do that.
#   - Requires optional and variadic arguments in compounds
# - Hack the detector in regen to recognize VentureSPRecords in
#   structures
#   - Problem: will be a (small?) performance hit, due to inspecting
#     every structure every time
#   - Problem: not clear whether the result will satisfy the intended
#     invariants, because I no longer remember what the invariants
#     are.
#  - Migrate the responsibility for SPRefs into the primitive maker
#    SPs (possibly including the current detector as a convenience).
#    - Not clear how to do this or whether it will work.
#  - Don't worry about it, since the inference SPs are currently only
#    used by the untraced backend anyway.
#
# Decision: Leaving it.

class MadeInferPrimitiveOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, exp):
    self.exp = [name] + exp
  def simulate(self, args):
    engine = args.operandValues()[0]
    ans = engine.primitive_infer(self.exp)
    return (ans, engine)

class MadeEngineMethodInferOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, operands, desc=None):
    self.name = name
    self.operands = operands
    self.desc = desc
  def simulate(self, args):
    engine = args.operandValues()[0]
    ans = getattr(engine, self.name)(*self.operands)
    return (ans, engine)
  def description(self, _name):
    return self.desc

class VentureNestedRiplMethodError(VentureError):
  """This exception means that this SP attempted a recursive Ripl operation which failed."""
  def __init__(self, message, cause, stack, addr):
    super(VentureNestedRiplMethodError, self).__init__(message)
    self.cause = cause
    self.stack = stack
    self.addr = addr

  def __str__(self):
    return str(self.cause)

class MadeRiplMethodInferOutputPSP(psp.LikelihoodFreePSP):
  def __init__(self, name, operands, desc=None):
    self.name = name
    self.operands = operands
    self.desc = desc
  def simulate(self, args):
    eng = args.operandValues()[0]
    ripl = eng.engine.ripl
    arguments = [o.asStackDict() for o in self.operands]
    try:
      ans = getattr(ripl, self.name)(*arguments, type=True) # Keep the stack dict
    except VentureException as err:
      import sys
      info = sys.exc_info()
      raise VentureNestedRiplMethodError("Nested ripl operation signalled an error", err, info, self.addr), None, info[2]
    try:
      ans_vv = v.VentureValue.fromStackDict(ans) if ans is not None else v.VentureNil()
    except VentureTypeError:
      # Do not return values that cannot be reconstructed from stack
      # dicts (e.g., SPs)
      ans_vv = v.VentureNil()
    return (ans_vv, eng)
  def description(self, _name):
    return self.desc

class MadeActionOutputPSP(psp.DeterministicPSP):
  def __init__(self, f, operands, desc=None):
    self.f = f
    self.operands = operands
    self.desc = desc
  def simulate(self, args):
    ans = self.f(*self.operands)
    return (ans, args.operandValues()[0])
  def description(self, _name):
    return self.desc

def infer_action_type(return_type):
  func_type = sp.SPType([t.ForeignBlobType()], t.PairType(return_type, t.ForeignBlobType()))
  ans_type = RecordType("inference_action", "returning " + return_type.name())
  ans_type.field_type = func_type
  return ans_type

def infer_action_maker_type(args_types, return_type=None, **kwargs):
  # Represent the underlying trace as a ForeignBlob for now.
  if return_type is None:
    return_type = t.NilType()
  return sp.SPType(args_types, infer_action_type(return_type), **kwargs)

def typed_inf_sp(name, tp, klass, desc=""):
  assert isinstance(tp, sp.SPType)
  return no_request(psp.TypedPSP(InferPrimitiveOutputPSP(name, klass=klass, desc=desc, tp=tp.return_type), tp))

def trace_method_sp(name, tp, desc=""):
  return [ name, typed_inf_sp(name, tp, MadeInferPrimitiveOutputPSP, desc) ]

def engine_method_sp(name, tp, desc="", method_name=None):
  if method_name is None:
    method_name = name
  return [ name, typed_inf_sp(method_name, tp, MadeEngineMethodInferOutputPSP, desc) ]

def ripl_method_sp(name, tp, desc="", method_name=None):
  if method_name is None:
    method_name = name
  return [ name, typed_inf_sp(method_name, tp, MadeRiplMethodInferOutputPSP, desc) ]

def sequenced_sp(f, tp, desc=""):
  "This is for SPs that should be able to participate in do blocks but don't actually read the state (e.g., for doing IO)"
  # TODO Assume they are all deterministic, for now.
  return no_request(psp.TypedPSP(InferPrimitiveOutputPSP(f, klass=MadeActionOutputPSP, desc=desc, tp=tp.return_type), tp))

def transition_oper_args_types(extra_args = None):
  # ExpressionType reasonably approximates the mapping I want for scope and block IDs.
  return [t.AnyType("scope : object"), t.AnyType("block : object")] + (extra_args if extra_args is not None else []) + [t.IntegerType("transitions : int")]

def transition_oper_type(extra_args = None, **kwargs):
  return infer_action_maker_type(transition_oper_args_types(extra_args), **kwargs)

def par_transition_oper_type(extra_args = None, **kwargs):
  other_args = transition_oper_args_types(extra_args)
  return infer_action_maker_type(other_args + [t.BoolType("in_parallel : bool")], min_req_args=len(other_args), **kwargs)

def macro_helper(name, tp):
  return engine_method_sp("_" + name, tp, method_name=name, desc="""\
A helper function for implementing the eponymous inference macro.

Calling it directly is likely to be difficult and unproductive. """)

def ripl_macro_helper(name, tp):
  return ripl_method_sp("_" + name, tp, method_name=name, desc="""\
A helper function for implementing the eponymous inference macro.

Calling it directly is likely to be difficult and unproductive. """)

def assert_fun(test, msg=""):
  # TODO Raise an appropriate Venture exception instead of crashing Python
  assert test, msg

def print_fun(*args):
  def convert_arg(arg):
    if isinstance(arg, VentureForeignBlob) and isinstance(arg.getForeignBlob(), Dataset):
      return arg.getForeignBlob().asPandas()
    else:
      return arg
  if len(args) == 1:
    print convert_arg(args[0])
  else:
    print [convert_arg(a) for a in args]

def plot_fun(spec, dataset):
  spec = t.ExpressionType().asPython(spec)
  if isinstance(dataset, Dataset):
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names)
  else:
    # Assume a raw data frame
    PlotSpec(spec).plot(dataset, list(dataset.columns.values))

def plot_to_file_fun(basenames, spec, dataset):
  filenames = t.ExpressionType().asPython(basenames)
  spec = t.ExpressionType().asPython(spec)
  if isinstance(dataset, Dataset):
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names, _format_filenames(filenames, spec))
  else:
    PlotSpec(spec).plot(dataset, list(dataset.columns.values), _format_filenames(filenames, spec))

def _format_filenames(filenames,spec):
  if isinstance(filenames, basestring) or isinstance(filenames, v.VentureString):
    if isinstance(filenames, v.VentureString):
      filenames = filenames.getString()
    if isinstance(spec, basestring) or isinstance(spec, v.VentureString):
      return [filenames + '.png']
    else:
      raise VentureValueError('The number of specs must match the number of filenames.')
  else:
    if isinstance(spec, list) and len(spec) == len(filenames):
      return [filename + '.png' for filename in filenames]
    else:
      raise VentureValueError('The number of specs must match the number of filenames.')

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
Run a Gibbs sampler that computes the local conditional by enumeration.

All the random choices identified by the scope-block pair must be
discrete.

The `transitions` argument specifies how many transitions of the
chain to run.

The `in-parallel` argument, if supplied, toggles parallel evaluation
of the local conditional.  Parallel evaluation is only available in the
Puma backend, and is on by default."""),

  trace_method_sp("emap", par_transition_oper_type(), desc="""\
Deterministically move to the local conditional maximum (computed by
enumeration).

All the random choices identified by the scope-block pair must be
discrete.

The ``transitions`` argument specifies how many times to do this.
Specifying more than one transition is redundant unless the ``block``
is `one`.

The ``in-parallel`` argument, if supplied, toggles parallel evaluation
of the local conditional.  Parallel evaluation is only available in
the Puma backend, and is on by default."""),

  trace_method_sp("func_pgibbs",
                  par_transition_oper_type([t.IntegerType("particles : int")]),
                  desc="""\
Move to a sample of the local conditional by particle Gibbs.

The ``block`` must indicate a sequential grouping of the random
choices in the `scope`.  This can be done by supplying the keyword
`ordered` as the block, or the value of calling `ordered_range`.

The ``particles`` argument specifies how many particles to use in the
particle Gibbs filter.

The ``transitions`` argument specifies how many times to do this.

The ``in-parallel`` argument, if supplied, toggles per-particle
parallelism.  Parallel evaluation is only available in the Puma
backend, and is on by default. """),

  trace_method_sp("pgibbs",
                  par_transition_oper_type([t.IntegerType("particles : int")]),
                  desc="""\
Like `func_pgibbs` but reuse a single trace instead of having several.

The performance is asymptotically worse in the sequence length, but
does not rely on stochastic procedures being able to functionally
clone their auxiliary state.

The only reason to use this is if you know you want to. """),

  trace_method_sp("func_pmap",
                  par_transition_oper_type([t.IntegerType("particles : int")]),
                  desc="""\
Like func_pgibbs, but deterministically
select the maximum-likelihood particle at the end instead of sampling.

Iterated applications of func_pmap are guaranteed to grow in likelihood
(and therefore do not converge to the conditional)."""),

  trace_method_sp("meanfield",
                  transition_oper_type([t.IntegerType("training_steps : int")]),
                  desc="""\
Sample from a mean-field variational approximation of the local conditional.

The mean-field approximation is optimized with gradient ascent.  The
`training_steps` argument specifies how many steps to take.

The `transitions` argument specifies how many times to do this.

Note: There is currently no way to save the result of training the
variational approximation to be able to sample from it many times. """),

  trace_method_sp("print_scaffold_stats", transition_oper_type(), desc="""\
Print some statistics about the requested scaffold.

This may be useful as a diagnostic.

The `transitions` argument specifies how many times to do this;
this is not redundant if the `block` argument is `one`."""),

  trace_method_sp("nesterov",
                  transition_oper_type([t.NumberType("step_size : number"), t.IntegerType("steps : int")]),
                  desc="""\
Move deterministically toward the maximum of the local conditional by
Nesterov-accelerated gradient ascent.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

The gradient is of the log conditional.

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
                  transition_oper_type([t.NumberType("step_size : number"), t.IntegerType("steps : int")]),
                  desc="""\
Move deterministically toward the maximum of the local conditional 
gradient ascent.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

This is just like `nesterov`, except without the Nesterov
correction. """),

  trace_method_sp("hmc",
                  transition_oper_type([t.NumberType("step_size : number"), t.IntegerType("steps : int")]),
                  desc="""\
Run a Hamiltonian Monte Carlo transition kernel.

Not available in the Puma backend.  Not all the builtin procedures
support all the gradient information necessary for this.

The presence of discrete random choices in the scope-block pair will
not prevent this inference strategy, but none of the discrete
choices will be moved.

The ``step_size`` argument gives the step size of the integrator used
by HMC.

The ``steps`` argument gives how many steps to take in each HMC
trajectory.

The ``transitions`` argument specifies how many times to do this."""),

  trace_method_sp("rejection", transition_oper_type([t.NumberType("attempt_bound : number")], min_req_args=2), desc="""\
Sample from the local conditional by rejection sampling.

Not available in the Puma backend.  Not all the builtin procedures
support all the density bound information necessary for this.

The ``attempt_bound`` bound argument, if supplied, indicates how many
attempts to make.  If no sample is accepted after that many trials,
stop, and leave the local state as it was.  Warning: bounded rejection
is not a Bayes-sound inference algorithm.  If `attempt_bound` is not
given, keep trying until acceptance (possibly leaving the session
unresponsive).  Note: if three arguments are supplied, the last one is
taken to be the number of transitions, not the attempt bound.

The ``transitions`` argument specifies how many times to do this.
Specifying more than 1 transition is redundant if the `block` is
anything other than `one`. """),

  trace_method_sp("bogo_possibilize", transition_oper_type(min_req_args=2), desc="""\
Initialize the local inference problem to a possible state.

If the current local likelihood is 0, resimulate the local prior until
a non-zero likelihood state is found.

Notes:

- If the current state is possible, do nothing.

- This is different from rejection sampling because the distribution
  on results is not the conditional, but the prior conditioned on the
  likelihood being non-zero.  As such, it is likely to complete
  faster.

- This is different from likelihood weighting because a) it keeps
  trying automatically until it finds a possible state, and b) it does
  not modify the weight of the particle it is applied to (because if
  the scope and block are other than ``default all`` it is not clear
  what the weight should become).

- Does not change the particle weight, because the right one is not
  obvious for general scaffolds, or for the case where the state was
  possible to begin with.  If you're using ``bogo_possibilize(default,
  all)`` for pure initialization from the prior, consider following it
  with::

    do(l <- global_log_likelihood,
       set_particle_log_weights(l))

The ``transitions`` argument specifies how many times to do this.
Specifying more than 1 transition is redundant if the `block` is
anything other than `one`. """),

  trace_method_sp("slice",
                  transition_oper_type([t.NumberType("w : number"), t.IntegerType("m : int")]),
                  desc="""\
Slice sample from the local conditonal of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the stepping-out procedure to find the slice.  The
`w` and `m` arguments parameterize the slice sampler in the standard
way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  trace_method_sp("slice_doubling",
                  transition_oper_type([t.NumberType("w : number"), t.IntegerType("p : int")]),
                  desc="""\
Slice sample from the local conditional of the selected random choice.

The scope-block pair must identify a single random choice, which
must be continuous and one-dimensional.

This kernel uses the interval-doubling procedure to find the slice.
The `w` and `p` arguments parameterize the slice sampler in the
standard way.

The `transitions` argument specifies how many transitions of the chain
to run."""),

  engine_method_sp("resample",
                   infer_action_maker_type([t.IntegerType("particles : int")]),
                   desc="""\
Perform an SMC-style resampling step.

The `particles` argument gives the number of particles to make.
Subsequent modeling and inference commands will be applied to each
result particle independently.

Future observations will have the effect of weighting the particles
relative to each other by the relative likelihoods of observing those
values in those particles.  The resampling step respects those
weights.

The new particles will be handled in series.  See the next procedures
for alternatives."""),

  engine_method_sp("resample_multiprocess",
                   infer_action_maker_type([t.IntegerType("particles : int"), t.IntegerType("max_processes : int")], min_req_args=1),
                   desc="""\
Like `resample`, but fork multiple OS processes to simulate the
resulting particles in parallel.

The ``max_processes`` argument, if supplied, puts a cap on the number of
processes to make.  The particles are distributed evenly among the
processes.  If no cap is given, fork one process per particle.

Subtlety: Collecting results (and especially performing further
resampling steps) requires inter-process communication, and therefore
requires serializing and deserializing any state that needs
transmitting.  `resample_multiprocess` is therefore not a drop-in
replacement for `resample`, as the former will handle internal
states that cannot be serialized, whereas the latter will not.  """),

  engine_method_sp("resample_serializing",
                   infer_action_maker_type([t.IntegerType("particles : int")]),
                   desc="""\
Like `resample`, but performs serialization the same way `resample_multiprocess` does.

Use this to debug serialization problems without messing with actually
spawning multiple processes.  """),

  engine_method_sp("resample_threaded",
                   infer_action_maker_type([t.IntegerType("particles : int")]),
                   desc="""\
Like `resample_multiprocess` but uses threads rather than actual processes, and does not serialize, transmitting objects in shared memory instead.

Python's global interpreter lock is likely to prevent any speed gains
this might have produced.

Might be useful for debugging concurrency problems without messing
with serialization and multiprocessing, but we expect such problems to
be rare. """),

  engine_method_sp("resample_thread_ser",
                   infer_action_maker_type([t.IntegerType("particles : int")]),
                   desc="""\
Like `resample_threaded`, but serializes the same way `resample_multiprocess` does.

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
                   infer_action_maker_type([t.ExpressionType("scope : object"), t.ExpressionType("block : object")]),
                   desc="""\
Diversify the current particle set to represent the local conditional exactly.

Specifically:

1) Compute the local conditional by enumeration of all possible values
   in the given scope and block

2) Fork every extant particle as many times are there are values

3) Give each new particle a relative weight proportional to the
   relative weight of its ancestor particle times the conditional 
   probability of the chosen value.

Unlike most inference SPs, this transformation is deterministic.

This is useful together with `collapse_equal` and
`collapse_equal_map` for implementing certain kinds of dynamic
programs in Venture. """),

  engine_method_sp("collapse_equal",
                   infer_action_maker_type([t.ExpressionType("scope : object"), t.ExpressionType("block : object")]),
                   desc="""\
Collapse the current particle set to represent the local conditional less redundantly.

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

This is useful together with `enumerative_diversify` for
implementing certain kinds of dynamic programs in Venture. """),

  engine_method_sp("collapse_equal_map",
                   infer_action_maker_type([t.ExpressionType("scope : object"), t.ExpressionType("block : object")]),
                   desc="""\
Like `collapse_equal` but deterministically retain the max-weight particle.

And leave its weight unaltered, instead of adding in the weights of
all the other particles in the bin. """),

  trace_method_sp("draw_scaffold", transition_oper_type(), desc="""\
Draw a visual representation of the scaffold indicated by the given scope and block.

This is useful for debugging.  You probably do not want to specify more than 1 transition."""),

  trace_method_sp("subsampled_mh",
                  transition_oper_type([t.IntegerType("Nbatch : int"), t.IntegerType("k0 : int"), t.NumberType("epsilon : number"),
                                        t.BoolType("useDeltaKernels : bool"), t.NumberType("deltaKernelArgs : number"), t.BoolType("updateValues : bool")]),
                  desc="""\
Run a subsampled Metropolis-Hastings kernel

per the Austerity MCMC paper.

Note: not all dependency structures that might occur in a scaffold are supported.  See `subsampled_mh_check_applicability`.

Note: the resulting execution history may not actually be possible, so
may confuse other transition kernels.  See `subsampled_mh_make_consistent`
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
                  transition_oper_type([t.BoolType("useDeltaKernels : bool"), t.NumberType("deltaKernelArgs : number"), t.BoolType("updateValues : bool")]),
                  desc="""\
Fix inconsistencies introduced by subsampled MH."""),

  trace_method_sp("mh_kernel_update",
                  transition_oper_type([t.BoolType("useDeltaKernels : bool"), t.NumberType("deltaKernelArgs : number"), t.BoolType("updateValues : bool")]),
                  desc="""\
Run a normal `mh` kernel, tolerating inconsistencies introduced by previous subsampled MH."""),

  trace_method_sp("gibbs_update", par_transition_oper_type(), desc="""\
Run a normal `gibbs` kernel, tolerating inconsistencies introduced by previous subsampled MH. """),

  trace_method_sp("pgibbs_update",
                  par_transition_oper_type([t.IntegerType("particles : int")]),
                  desc="""\
Run a normal `pgibbs` kernel, tolerating inconsistencies introduced by previous subsampled MH."""),

  engine_method_sp("incorporate", infer_action_maker_type([]), desc="""\
Explicitly make the history consistent with observations.

Specifically, modify the execution history so that the values of
variables that have been observed since the last `incorporate` match
the given observations.  If there are multiple particles, also adjust
their relative weights by the relative likelihoods of the
observations being incorporated.

This is done automatically at the end of every `observe` command,
but is also provided explicitly in case is proves needful.

Note: In the future, VentureScript may implement various different
incorporation algorithms, in which case explicit incorporation may become
necessary again.
"""),

  engine_method_sp("log_likelihood_at",
                   infer_action_maker_type([t.AnyType("scope : object"), t.AnyType("block : object")], return_type=t.ArrayUnboxedType(t.NumberType())),
                   desc="""\
Compute and return the value of the local log likelihood at the given scope and block.

If there are stochastic nodes in the conditional regeneration graph,
reuses their current values.  This could be viewed as a one-sample
estimate of the local likelihood.

log_likelihood_at(default, all) is not the same as ``getGlobalLogScore``
because it does not count the scores of any nodes that cannot report
likelihoods, or whose existence is conditional.  `log_likelihood_at` also
treats exchangeably coupled nodes correctly.

Compare `log_joint_at`."""),

  engine_method_sp("log_joint_at",
                   infer_action_maker_type([t.AnyType("scope : object"), t.AnyType("block : object")], return_type=t.ArrayUnboxedType(t.NumberType())),
                   desc="""\
Compute and return the value of the local log joint density at the given scope and block.

The principal nodes must be able to assess.  Otherwise behaves like
log_likelihood_at, except that it includes the log densities of
non-observed stochastic nodes."""),

  engine_method_sp("particle_log_weights",
                   infer_action_maker_type([], t.ArrayUnboxedType(t.NumberType())),
                   desc="""\
Return the weights of all extant particles as an array of numbers (in log space).
"""),

  engine_method_sp("set_particle_log_weights",
                   infer_action_maker_type([t.ArrayUnboxedType(t.NumberType())]),
                   desc="""\
Set the weights of the particles to the given array.  It is an error if the length of the array differs from the number of particles. """),

  engine_method_sp("for_each_particle",
                   infer_action_maker_type([t.AnyType("<action>")], t.ListType()), desc="""\
Run the given inference action once for each particle in the
model. The inference action is evaluated independently for each
particle, and is not allowed to contain modeling commands (``assume``,
``observe``, ``predict``, ``forget``, ``freeze``).
"""),

  engine_method_sp("load_plugin", infer_action_maker_type([t.SymbolType("filename")], return_type=t.AnyType(), variadic=True), desc="""\
Load the plugin located at <filename>.

Any additional arguments to `load_plugin` are passed to the plugin's
``__venture_start__`` function, whose result is returned.

XXX: Currently, extra arguments must be VentureSymbols, which are
unwrapped to Python strings for the plugin.
"""),

  macro_helper("call_back", infer_action_maker_type([t.AnyType()], return_type=t.AnyType(), variadic=True)),
  macro_helper("collect", infer_action_maker_type([t.AnyType()], return_type=t.ForeignBlobType("<dataset>"), variadic=True)),

  engine_method_sp("printf", infer_action_maker_type([t.ForeignBlobType("<dataset>")]), desc="""\
Print model values collected in a dataset.

This is a basic debugging facility."""),

  ["plot", deterministic_typed(plot_fun, [t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")], t.NilType(), descr="""\
Plot a data set according to a plot specification.

Example::

    define d = empty()
    assume x = normal(0, 1)
    infer accumulate_dataset(1000,
              do(mh(default, one, 1),
                 collect(x)))
    plot("c0s", d)
    
will do 1000 iterations of `mh` collecting some standard data and
the value of ``x``, and then show a plot of the ``x`` variable (which
should be a scalar) against the iteration number (from 1 to 1000),
colored according to the global log score.  See `collect`
for details on collecting and labeling data to be plotted.

The format specifications are inspired loosely by the classic
printf.  To wit, each individual plot that appears on a page is
specified by some line noise consisting of format characters
matching the following regex::

    [<geom>]*(<stream>?<scale>?){1,3}

specifying

- the geometric objects to draw the plot with, and
- for each dimension (x, y, and color, respectively)
    - the data stream to use
    - the scale

The possible geometric objects are:

- _p_oint,
- _l_ine,
- _b_ar, and
- _h_istogram

The possible data streams are:

- _<an integer>_ that column in the data set, 0-indexed,
- _%_ the next column after the last used one
- iteration _c_ounter,
- _t_ime (wall clock, since the beginning of the Venture program),
- log _s_core, and
- pa_r_ticle

The possible scales are:

- _d_irect, and
- _l_ogarithmic

If one stream is indicated for a 2-D plot (points or lines), the x
axis is filled in with the iteration counter.  If three streams are
indicated, the third is mapped to color.

If the given specification is a list, make all those plots at once.
""")],

  engine_method_sp("plotf", infer_action_maker_type([t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")]), desc="""\
Plot a data set according to a plot specification.

This is identical to `plot`, except it's an inference action,
so can participate in `do` blocks.

Example::

    do(assume x, normal(0, 1),
       ...
       plotf("c0s", d))
"""),

  ["plot_to_file", deterministic_typed(plot_to_file_fun, [t.AnyType("<basename>"), t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")], t.NilType(), descr="""\
Save plot(s) to file(s).

Like `plot`, but save the resulting plot(s) instead of displaying on screen.
Just as ``<spec>`` may be either a single expression or a list, ``<basenames>`` may
either be a single symbol or a list of symbols. The number of basenames must
be the same as the number of specifications.

Examples:
  plot_to_file("basename", "spec", <expression> ...) saves the plot specified by
    the spec in the file "basename.png"
  plot_to_file(quote(basename1, basename2), (quote(spec1, spec2)), <expression> ...) saves
    the spec1 plot in the file basename1.png, and the spec2 plot in basename2.png.
""")],

  engine_method_sp("plotf_to_file", infer_action_maker_type([t.AnyType("<basename>"), t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")]), desc="""\
Save plot(s) to file(s).

Like `plotf`, but save the resulting plot(s) instead of displaying on screen.
See `plot_to_file`.
"""),

  engine_method_sp("sweep", infer_action_maker_type([t.ForeignBlobType("<dataset>")]), desc="""\
Print the iteration count.

Extracts the last row of the supplied inference Dataset and prints its iteration count.
"""),

  ripl_macro_helper("assume", infer_action_maker_type([t.AnyType("<symbol>"), t.AnyType("<expression>"), t.AnyType("<label>")], return_type=t.AnyType(), min_req_args=2)),
  ripl_macro_helper("observe", infer_action_maker_type([t.AnyType("<expression>"), t.AnyType(), t.AnyType("<label>")], min_req_args=2)),
  macro_helper("force", infer_action_maker_type([t.AnyType("<expression>"), t.AnyType()])),
  ripl_macro_helper("predict", infer_action_maker_type([t.AnyType("<expression>"), t.AnyType("<label>")], return_type=t.AnyType(), min_req_args=1)),
  macro_helper("sample", infer_action_maker_type([t.AnyType("<expression>")], return_type=t.AnyType())),
  macro_helper("sample_all", infer_action_maker_type([t.AnyType("<expression>")], return_type=t.ListType())),
  macro_helper("extract_stats", infer_action_maker_type([t.AnyType("<expression>")], return_type=t.AnyType())),

  ripl_method_sp("forget", infer_action_maker_type([t.AnyType("<label>")]), desc="""\
Forget an observation, prediction, or unused assumption.

Removes the directive indicated by the label argument from the
model.  If an assumption is forgotten, the symbol it binds
disappears from scope; the behavior if that symbol was still
referenced is unspecified.
"""),

  ripl_method_sp("freeze", infer_action_maker_type([t.AnyType("<label>")]), desc="""\
Freeze an assumption to its current sample.

Replaces the assumption indicated by the label argument with a
constant whose value is that assumption's current value (which may
differ across particles).  This has the effect of preventing future
inference on that assumption, and decoupling it from its (former)
dependecies, as well as reclaiming any memory of random choices
that can no longer influence any toplevel value.

Together with forget, freeze makes it possible for particle filters
in Venture to use model memory independent of the sequence length.
"""),

  ["empty", deterministic_typed(lambda *args: Dataset(), [], t.ForeignBlobType("<dataset>"), descr="""\
Create an empty dataset `into` which further `collect` ed stuff may be merged.
  """)],

  ["into", sequenced_sp(lambda orig, new: orig.merge_bang(new), infer_action_maker_type([t.ForeignBlobType(), t.ForeignBlobType()]), desc="""\
Destructively merge the contents of the second argument into the
first.

Right now only implemented on datasets created by `empty` and
`collect`, but in principle generalizable to any monoid.  """)],

  # Hackety hack hack backward compatibility
  ["ordered_range", deterministic_typed(lambda *args: (t.VentureSymbol("ordered_range"),) + args,
                                        [t.AnyType()], t.ListType(), variadic=True)],

  ["assert", sequenced_sp(assert_fun, infer_action_maker_type([t.BoolType(), t.SymbolType("message")], min_req_args=1), desc="""\
Check the given boolean condition and raise an error if it fails.
""")],

  ["print", deterministic_typed(print_fun, [t.AnyType()], t.NilType(), variadic=True, descr="""\
Print the given values to the terminal.
""")],

  engine_method_sp("new_model", infer_action_maker_type([t.SymbolType()], t.ForeignBlobType("<model>"), min_req_args=0), desc="""\
Create an new empty model.

The symbol, if supplied, gives the name of the backend to use, either
``puma`` or ``lite``.  If omitted, defaults to the same backend as the
current implicit model.

This is an inference action rather than a pure operation due to
implementation accidents. [It reads the Engine to determine the
default backend to use and for the
registry of bound foreign sps.]

 """),

  engine_method_sp("fork_model", infer_action_maker_type([t.SymbolType()], t.ForeignBlobType("<model>"), min_req_args=0), desc="""\
Create an new model by copying the state of the current implicit model.

The symbol, if supplied, gives the name of the backend to use, either
``puma`` or ``lite``.  If omitted, defaults to the same backend as the
current implicit model.

 """),

  engine_method_sp("in_model", infer_action_maker_type([t.ForeignBlobType("<model>"), t.AnyType("<action>")], t.PairType(t.AnyType(), t.ForeignBlobType("<model>"))), desc="""\
Run the given inference action against the given model.

Returns a pair consisting of the result of the action and the model, which is also mutated.

This is itself an inference action rather than a pure operation due
to implementation accidents. [It invokes a method on the Engine
to actually run the given action].
"""),

  engine_method_sp("model_import_foreign", infer_action_maker_type([t.SymbolType("<name>")]), desc="""\
Import the named registered foregin SP into the current model.

This is typically only necessary in conjunction with `new_model`,
because foreign SPs are automatically imported into the model that
is ambient at the time the foreign SP is bound by the ripl (which is
usually the toplevel model).

The name must refer to an SP that was previously registered with
Venture via `ripl.register_foreign_sp` or `ripl.bind_foreign_sp`.
Binds that symbol to that procedure in the current model.
"""),

  engine_method_sp("select", infer_action_maker_type([t.AnyType("scope : object"), t.AnyType("block : object")], t.ForeignBlobType("subproblem")), desc="""\
Select the subproblem indicated by the given scope and block from the current model.

Does not interoperate with multiple particles, or with stochastic
subproblem selection.

"""),

  engine_method_sp("detach", infer_action_maker_type([t.ForeignBlobType("<subproblem>")], t.PairType(t.NumberType("weight"), t.ForeignBlobType("<rhoDB>"))), desc="""\
Detach the current model along the given subproblem.

Return the current likelihood at the fringe, and a database of the old
values that is suitable for restoring the current state (e.g., for
rejecting a proposal).

Does not interoperate with multiple particles, or with custom proposals.

"""),

  engine_method_sp("regen", infer_action_maker_type([t.ForeignBlobType("<subproblem>")], t.NumberType("weight")), desc="""\
Regenerate the current model along the given subproblem.

Return the new likelihood at the fringe.

Does not interoperate with multiple particles, or with custom proposals.

"""),

  engine_method_sp("restore", infer_action_maker_type([t.ForeignBlobType("<subproblem>"), t.ForeignBlobType("<rhoDB>")], t.NumberType("weight")), desc="""\
Restore a former state of the current model along the given subproblem.

Does not interoperate with multiple particles.

"""),

  engine_method_sp("detach_for_proposal", infer_action_maker_type([t.ForeignBlobType("<subproblem>")], t.PairType(t.NumberType("weight"), t.ForeignBlobType("<rhoDB>"))), desc="""\
Detach the current model along the given subproblem, returning the
local posterior.

Differs from detach in that it includes the log densities of the principal
nodes in the returned weight, so as to match regen_with_proposal. The
principal nodes must be able to assess.

Return the current posterior at the fringe, and a database of the old
values for restoring the current state.

Does not interoperate with multiple particles.

"""),

  engine_method_sp("regen_with_proposal", infer_action_maker_type([t.ForeignBlobType("<subproblem>"), t.ListType()], t.NumberType("weight")), desc="""\
Regenerate the current model along the given subproblem from the
given values.

Differs from regen in that it deterministically moves the principal nodes
to the given values rather than resimulating them from the prior, and
includes the log densities of those nodes in the returned weight. The
principal nodes must be able to assess.

Return the new posterior at the fringe.

Does not interoperate with multiple particles.

"""),

  engine_method_sp("get_current_values", infer_action_maker_type([t.ForeignBlobType("<subproblem>")], t.ListType()), desc="""\
Get the current values of the principal nodes of the given subproblem.

Does not interoperate with multiple particles.

"""),

  ripl_method_sp("draw_subproblem", infer_action_maker_type([t.AnyType("<subproblem>")]), desc="""\
  Draw a subproblem by printing out the source code of affected random choices.

"""),

  engine_method_sp("pyexec", infer_action_maker_type([t.SymbolType("<code>")]), desc="""\
Execute the given string as Python code, via exec.

The code is executed in an environment where the RIPL is accessible
via the name ``ripl``.  Values from the ambient inference program are
not directly accessible.  The environment against which `pyexec` is
executed persists across invocations of `pyexec` and `pyeval`.
"""),

  engine_method_sp("pyeval", infer_action_maker_type([t.SymbolType("<code>")], return_type=t.AnyType()), desc="""\
Evaluate the given string as a Python expression, via eval.

The code is executed in an environment where the RIPL is accessible
via the name ``ripl``.  Values from the ambient inference program are
not directly accessible.  The environment against which `pyeval` is
evaluated persists across invocations of `pyexec` and `pyeval`.
"""),

]

inferenceKeywords = [ "default", "all", "none", "one", "ordered" ]
