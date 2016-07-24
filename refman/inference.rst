.. _inference-section:

Inference Syntax Reference
==========================

Introduction
------------

The VentureScript inference language is the language in which the toplevel
VentureScript program is written.  It is actually the same language as the
VentureScript modeling language, except with several additional predefined
procedures and special forms.

VentureScript inference programs are effectively evaluated in a context
where the underlying model trace is available as a reified object, on
which built-in inference procedures can operate. [#]_

Block Structure
---------------

Like JavaScript, the organizing syntactic element of VentureScript is
the *block*: a list of *statements* surrounded by curly braces and
separated by parentheses.  VentureScript has the following kinds of
statements:

.. _let_binding:
.. object:: let <var> = <expression>;

  Bind the variable on the left hand side to the value of the
  expression on the right hand side for the remainder of the block.

  Note 1: This is not assignment: if the variable was already in
  scope, it is shadowed, not mutated; at the end of the block, the old
  value will be visible again.

  Note 2: If the expression produces an inference action, that action
  is not performed, but stored in the variable for later use.  See
  `<-`.

.. _monad_binding:
.. object:: <var> <- <action>;

  Perform the inference action on the right hand side and bind the
  returned value to the variable on the left hand side.

  Note 1: This is not assignment: if the variable was already in
  scope, it is shadowed, not mutated; at the end of the block, the old
  value will be visible again.

  Note 2: It is an error for the expression to produce a value that is
  not an inference action.  For binding the results of pure
  computations, see `let`.

.. _mv_binding:
.. object:: let (<var1>, <var2>, ...) = <expression>;

  Multiple value bind.  The expression must return a list of `ref` s
  of the same length as the number of variables.  See also `values_list`.

.. _letrec_binding:
.. object:: letrec <var1> = <expression1>;
               and <var2> = <expression2>;
               ...

  Mutually recursive binding.  The contiguous chain of `and`
  statements are grouped together with the `letrec` statement at the
  beginning, and all the variables are in scope in all the defining
  expressions and the rest of the block, analogously to the same
  construct in Scheme.  The name stands for "let, recursively".  This
  is useful for defining mutually recursive procedures::

      letrec even = (n) -> { if (n == 0) { true  } else {  odd(n - 1) } };
         and odd  = (n) -> { if (n == 0) { false } else { even(n - 1) } };

.. _effect:
.. object:: <action>

  Just evaluate the expression.  If this is the last statement of the
  block, the return value of the whole block is the result of
  evaluating the expression.

Note that all of these affordances appear as expressions as well.  In
fact, the block structure in VentureScript is just syntactic sugar for
nested binding expressions of various kinds.

Inference control with tags and subproblems
-------------------------------------------

VentureScript permits the user to control the strategy and focus of
inference activity with the notion of the *subproblem*.  Any set of
random choices in a VentureScript model defines a `local subproblem`,
which is the problem of sampling from the posterior on those choices,
conditioned on keeping the rest of the execution history fixed.
Subproblem decomposition is useful because progress in distribution on
a subproblem constitutes progress on the overall problem as well.

It is typical to prepare a model for inference control by tagging some
expressions with tags that can later be referenced when selecting a
subproblem to operate on.  VentureScript provides syntactic sugar
for tagging model expressions::

    something #tag1
    something_else #tag2:value

The first form just associates the `something` expression with the tag
named `tag1`.  The second form associates the `something_else`
expression with the tag named `tag2` with the value computed by the
`value` expression.

For example, a typical simple Dirichlet process mixture model (over
Bernoulli vectors) might be implemented and tagged like this::

    assume assign   = make_crp(1);
    assume z        = mem((i) ~> { assign() #clustering });     // The partition induced by the DP
    assume pct      = mem((d) ~> { gamma(1.0, 1.0) #hyper:d }); // Per-dimension hyper prior
    assume theta    = mem((z, d) ~> { beta(pct(d), pct(d)) #compt:d });   // Per-component latent
    assume datum    = mem((i, d) ~> {{
      cmpt ~ z(i);
      weight ~ theta(cmpt, d);
      flip(weight)} #row:i #col:d });   // Per-datapoint random choices

VentureScript provides a path-like syntax for identifying random
choices in a model on which inference might then be applied.  The `/`
(forward slash) operator is analogous to a UNIX directory separator:
it means "apply the pattern on the right to subchoices of the choices
selected on the right" (and a leading `/` means "search for the
choices on right in the whole model").  For example::

    /?hyper               // select all choices tagged with the "hyper" tag
    /?row==3              // select all choices involved in the third row
    /?row==3/?clustering  // select only the cluster assignment for the third row

Random choice selections can also be computed programmatically with
the procedures beginning with `by_`, below.

A complete subproblem definition includes not only the random choices
of interest, but also additional information, such as how to treat
which of their consequences (likelihood-free choices have to be
resampled, choices that can report likelihoods may be resampled or may
be kept, contributing to the acceptance ratio, etc).  VentureScript
currently provides one operation to convert a selection of random
choices into a subproblem, namely `minimal_subproblem`.  That
subproblem may then be passed to an inference operation like `mh` to
actually operate on those choices.

Randomized proposal targets may be obtained with the
`random_singleton` procedure, which correctly accounts for the
acceptance correction due to the probability of selecting that
particular subproblem to work on.

Putting it all together, the inference tactic `default_markov_chain`
might be defined as::

    define default_markov_chain = (n) -> {
      repeat(n, mh(minimal_subproblem(random_singleton(by_extent(by_top())))))}

For compatibility with previous versions of VentureScript, all the
inference operators will also accept a tag and a tag value as two
separate arguments, and treat them as `minimal_subproblem(/?<tag>==<value>)`.

**Note**: The argument lists of the inference operators below
come out of Sphinx a bit weird.  The intent is that the "tag_value"
argument is required if and only if the "subproblem" argument is
actually a raw tag, and immediately follows it.

**Note 2**: The subproblem selection subsystem is not (yet)
implemented in the Puma backend.  If using Puma, use the tag/value
invocation form.

Any given random choice in an execution history can be tagged by an
arbitrary number of tags; but for each tag it has, it must be given a
unique value (if any).  The most locally assigned value wins.

Built-in Procedures for Inference
---------------------------------

All the procedures available in the modeling language can be used in
the inference language, too.  In addition, the following inference
procedures are available.

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
  apply to no random choices.  This is useful only for `collapse_equal`
  and `collapse_equal_map`.

- `ordered`: Make particle Gibbs operate on all blocks in order of block ID.

- `ordered_range(<block>, <block>)`: Make particle Gibbs operate on a
  range of blocks in order of block ID.

  Specifically, all the blocks whose IDs lie between the given lower
  and upper bounds.

Special Forms
-------------

All the macros available in the modeling language can be used in the
inference language, too.  In addition, the following inference macros
are available.

.. function:: loop(<kernel>)

  Run the given kernel continuously in a background thread.

  Available in Lite and Puma.

  Can only be used as the top level of the `infer` instruction:
  ``infer loop(something)``.

  Execute the `stop_continuous_inference` instruction to stop.

.. include:: inference-macros.gen

.. function:: unquote(<object>)

  Programmatically construct part of a model expression.

  All the ``<model-expression>`` s in the above special forms may be
  constructed programmatically.  An undecorated expression is taken
  literally, but if ``unquote(...)`` appears in such an expression,
  the code inside the unquote is executed **in the inference program**,
  and its result is spliced in to the model program.

  For example, suppose one wanted to observe every value in a data
  set, but allow the model to know the index of the observation (e.g.,
  to select observation models).  For this, every observed model
  expression needs to be different, but in a programmable manner.
  Here is a way to do that::

    define data = ...
    define observe_after = proc(i) {
      if (i < length(data)) {
         do(observe(obs_fun(unquote(i)), lookup(data, i)),  // (*)
            observe_after(i + 1))
      } else {
         pass
      }}
    infer observe_after(0)

  Note the use of unquote on the like marked ``(*)`` to construct
  different observe expressions for each data element.  To the
  underlying model, this will look like::

    observe obs_fun(0) = <val0>
    observe obs_fun(1) = <val1>
    observe obs_fun(2) = <val2>
    ...

.. rubric:: Footnotes

.. [#] For the interested, the way this is actually done is that each
   of the primitives documented here actually returns a procedure that
   accepts a reified object representing the sampled execution history
   of the model program, affects it, and returns a pair consisting of
   whatever value it wishes to return in the first slot, and the
   reified execution history in the second.  This is relevant if you
   wish to define additional inference abstractions in Venture, or
   more complex combinations of them than the provided ones.

   For those readers for whom this analogy is helpful, the above is
   exactly the type signature one would get by implementing a
   ``State`` monad on execution histories.  This is why the ``do``
   form is called ``do``.  The ``begin`` form is a simplification of
   ``do`` that drops all intermediate return values.  For the analogues
   of ``runState``, see `in_model` and `run`.  As of this writing, there are
   no analogues of ``get`` or ``put``.
