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

.. include:: inference-proc.gen

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

- `none`: Affect no choices in the scope.

  If given as a block keyword, `none` causes the inference procedure to
  apply to no random choices.  This is useful only for ``collapse_equal``
  and ``collapse_equal_map``.

- `ordered`: Make particle Gibbs operate on all blocks in order of block ID.

- `(ordered_range <block> <block>)`: Make particle Gibbs operate on a
  range of blocks in order of block ID.

  Specifically, all the blocks whose IDs lie between the given lower
  and upper bounds.

Special Forms
-------------

- `(loop (<kernel> ...))`: Run the given kernels in order continuously
  in a background thread.

  Available in Lite and Puma.

  Can only be used as the top level of the `infer` instruction:
  ``[infer (loop (stuff...))]``.

  Execute the ``[stop_continuous_inference]`` instruction to stop.

.. include:: inference-macros.gen

.. rubric:: Footnotes

.. [#] For the interested, the way this is actually done is that each
   of the primitives documented here actually returns a procedure that
   accepts a reified Trace, affects it, and returns it.  This is
   relevant if you wish to define additional inference abstractions in
   Venture, or more complex combinations of them than the provided
   ones.
