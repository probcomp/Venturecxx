Inference Syntax Reference (VenChurch)
======================================

Introduction
------------

The Venture inference language is the language in which arguments to
`infer` are written.  It is actually the same language as the Venture
modeling language, except with a few additional predefined procedures
and special forms.

Venture inference programs are effectively evaluated in a context
where the underlying model trace is available as a reified object, on
which built-in inference procedures can operate. [#]_

Scopes, Blocks, and the Local Posterior
---------------------------------------

Venture defines the notion of `inference scope` to allow the
programmer to control the parts of their model on which to apply
various inference procedures.  The idea is that a `scope` is some
collection of related random choices (for example, the states of a
hidden Markov model could be one scope, and the hyperparameters could
be another); and each scope is further subdivided into `block` s,
which are choices that ought to be reproposed together (the name is
meant to evoke the idea of block proposals).

Any given random choice in an execution history can exist in an
arbitrary number of scopes; but for each scope it is in it must be in
a unique block.  As such, a scope-block pair denotes a set of random
choices.

Any set of random choices defines a `local posterior`, which is the
posterior on those choices, conditioned on keeping the rest of the
execution history fixed.  Every inference method accepts a scope id
and a block id as its first two arguments, and operates only on those
random choices, with respect to that local posterior.

Built-in Procedures for Inference
---------------------------------

- `(mh <scope> <block> <transitions>)`: Run a Metropolis-Hastings
  kernel, proposing by resimulating the prior.

  The `transitions` argument specifies how many transitions of the
  chain to run.

- `(slice <scope> <block> <transitions>)`: Run a kernel slice sampling
  from the local posterior of the selected random choice.

  The scope-block pair must identify a single random choice, which
  must be continuous and one-dimensional.

  The `transitions` argument specifies how many transitions of the
  chain to run.

- `(gibbs <scope> <block> <transitions> [<in-parallel>])`: Run a Gibbs
  sampler that computes the local posterior by enumeration.

  All the random choices identified by the scope-block pair must be
  discrete.

  The `transitions` argument specifies how many transitions of the
  chain to run.

  The `in-parallel` argument, if supplied, toggles parallel evaluation
  of the local posterior.  Parallel evaluation is only available in
  the Puma backend, and is on by default.

- `(emap <scope> <block> <transitions> [<in-parallel>])`:
  Deterministically move to the local posterior maximum (computed by
  enumeration).

  All the random choices identified by the scope-block pair must be
  discrete.

  The `transitions` argument specifies how many times to do this.
  Specifying more than one transition is redundant unless the `block`
  is ``one``.

  The `in-parallel` argument, if supplied, toggles parallel evaluation
  of the local posterior.  Parallel evaluation is only available in
  the Puma backend, and is on by default.

- `(func_pgibbs <scope> <block> <particles> <transitions> [<in-parallel>])`:
  Move to a sample of the local posterior computed by particle Gibbs.

  The `block` must indicate a sequential grouping of the random
  choices in the `scope`.  This can be done by supplying the keyword
  ``ordered`` as the block, or the value of calling ``ordered_range``.

  The `particles` argument specifies how many particles to use in the
  particle Gibbs filter.

  The `transitions` argument specifies how many times to do this.

  The `in-parallel` argument, if supplied, toggles per-particle
  parallelism.  Parallel evaluation is only available in the Puma
  backend, and is on by default.

- `(pgibbs <scope> <block> <particles> <transitions> [<in-parallel>])`:
  Like ``func_pgibbs`` but reuse a single trace instead of having several.

  The performance is asymptotically worse in the sequence length, but
  does not rely on stochastic procedures being able to functionally
  clone their auxiliary state.

  The only reason to use this is if you know you want to.

- `(meanfield <scope> <block> <training_steps> <transitions>)`: Sample
  from a mean-field variational approximation of the local posterior.

  The mean-field approximation is optimized with gradient ascent.  The
  `training_steps` argument specifies how many steps to take.

  The `transitions` argument specifies how many times to do this.

  Note: There is currently no way to save the result of training the
  variational approximation to be able to sample from it many times.

- `(nesterov <scope> <block> <step_size> <steps> <transitions>)`: Move
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
  transition, not across transitions.

- `(map <scope> <block> <step_size> <steps> <transitions>)`: Move
  deterministically toward the maximum of the local posterior by
  gradient ascent.

  Not available in the Puma backend.  Not all the builtin procedures
  support all the gradient information necessary for this.

  This is just like ``nesterov``, except without the Nesterov
  correction.

- `(hmc <scope> <block> <step_size> <steps> <transitions>)`: Run a
  Hamiltonian Monte Carlo transition kernel.

  Not available in the Puma backend.  Not all the builtin procedures
  support all the gradient information necessary for this.

  The presence of discrete random choices in the scope-block pair will
  not prevent this inference strategy, but none of the discrete
  choices will be moved.

  The `step_size` argument gives the step size of the integrator used
  by HMC.

  The `steps` argument gives how many steps to take in each HMC
  trajectory.

  The `transitions` argument specifies how many times to do this.

- `(rejection <scope> <block> <transitions>)`: Sample from the local
  posterior by rejection sampling.

  Not available in the Puma backend.  Not all the builtin procedures
  support all the density bound information necessary for this.

  The `transitions` argument specifies how many times to do this.
  Specifying more than 1 transition is redundant if the `block` is
  anything other than ``one``.

- `(resample <particles>)`: Perform a resampling step.

  The `particles` argument gives the number of particles to make.
  Subsequent modeling and inference commands will be applied to each
  result particle independently.  Data reporting commands will talk to
  one distinguished particle, except ``peek_all``.

- `(incorporate)`: Make the history consistent with observations.

  This is done at the beginning of every `infer` command, but is
  provided explicitly for completeness.

Built-in Helpers
----------------

- `default`: The default scope.

  The default scope contains all the random choices, each in its own block.

- `one`: Mix over individual blocks in the scope.

  If given as a block keyword, `one` causes the inference procedure to
  uniformly choose one of the blocks in the scope on which it is
  invoked and apply to that.

- `all`: Affect all choices in the scope.

  If given as a block keyword, `all` causes the inference procedure to
  apply to all random choices in the scope.

- `ordered`: Make particle Gibbs operate on all blocks in order of block ID.

- `(ordered_range <block> <block>)`: Make particle Gibbs operate on a
  range of blocks in order of block ID.

  Specifically, all the blocks whose IDs lie between the given lower
  and upper bounds.

Special Forms
-------------

- `(cycle (<kernel> ...) <transitions>)`: Run a cycle kernel.

  Execute each of the given subkernels in order.

  The `transitions` argument specifies how many times to do this.

- `(mixture (<weight> <kernel> ...) <transitions>)`: Run a mixture kernel.

  Choose one of the given subkernels according to its weight and
  execute it.

  The `transitions` argument specifies how many times to do this.

- `(peek <expression> [<name>])`: Extract data from the underlying
  model during inference.

  Every time a `peek` inference command is executed, the given
  expression is sampled and its value is stored.  When inference
  completes, the data extracted is either returned, if Venture is
  being used as a library, or printed, if from the interactive
  console.

  The optional `name`, if supplied, serves as the key in the returned
  table of peek data.  If omitted, `name` defaults to a string
  representation of the given `expression`.

- `(peek_all <expression> [<name>])`: Like `peek`, but extract data
  from all available particles.

- `(plotf <spec> <expression> ...)`: Accumulate data for plotting.

  Every time a `plotf` command is executed, the given expressions are
  sampled and their values are stored.  When inference completes, the
  data extracted is either returned as a ``SpecPlot`` object, if
  Venture is being used as a library, or plotted on the screen, if
  from the interactive console.

  The two most useful methods of the ``SpecPlot`` are ``plot()``,
  which draws that plot on the screen, and ``dataset()``, which
  returns the stored data as a Pandas DataFrame.

- `(loop (<kernel> ...))`: Run the given kernels in order continuously
  in a background thread.

  Available in Lite and Puma.

  Can only be used as the top level of the `infer` instruction:
  ``[infer (loop (stuff...))]``.

  Execute the ``[stop_continuous_inference]`` instruction to stop.

.. rubric:: Footnotes

.. [#] For the interested, the way this is actually done is that each
   of the primitives documented here actually returns a procedure that
   accepts a reified Trace, affects it, and returns it.  This is
   relevant if you wish to define additional inference abstractions in
   Venture, or more complex combinations of them than the provided
   ones.
