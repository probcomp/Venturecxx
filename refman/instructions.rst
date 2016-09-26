Directive Cheatsheet
====================

Summary::

    assume symbol = expression
    observe expression = value
    predict expression
    forget directive_id
    freeze directive_id
    report directive_id
    force expression = value
    sample expression
    infer loop(expression)
    endloop
    define symbol = expression
    load filename
    clear
    list_directives
    ci_status

Directives
----------

The `assume`, `observe`, and `predict` operators, also called
*directives*, make up the core modeling language of VentureScript. Each
directive contains a modeling expression to be evaluated. At any time,
the probabilistic execution trace consists of all directives that have
been evaluated and not forgotten.  VentureScript maintains an index of
unique identifiers for directives so they can be referred to by other
operations.

- `assume symbol = expression`: declare and initialize a variable.

  Assume evaluates the `expression` and binds the result to ``symbol``
  in the global environment.

- `observe expression = value`: condition on observed data.

  The condition constrains the result of `expression` to be equal to
  `value`.

  An expression can only be constrained by an `observe` directive if
  its outermost procedure application is the result of a stochastic
  computation, rather than a deterministic one. For example, `observe
  normal(0, 1) = 0` is valid, but `observe normal(0, 1) + 1 = 0` is
  not, because `+` is a deterministic function of its arguments.

  `observe` generally has no effect on the distribution of values in
  the program until the next time inference is invoked.  The
  exceptions to this are: the observed value itself and deterministic
  consequecnes (which are changed to match the observation
  immediately), and the values of any new variables created after
  the `observe` is executed.

- `predict expression`: register a persistent prediction.

  Predict tracks the `expression`, allowing its value to be reported
  before or after inference.

  A `predict` directive is persistent, in the sense that it becomes
  part of the program history and will be maintained and potentially
  resampled during inference.  A `predict` ed expression may affect the
  evaluation of later expressions that are correlated or conditionally
  dependent.  To evaluate an expression non-persistently, use `sample`.

Directive manipulation
----------------------

In addition to the directives themselves, there are operators
`forget`, `freeze`, and `report` which manipulate directives.

- `forget directive_id`: remove a directive from the program history.

  Further inference will behave as if that directive had never been
  executed.

  Be careful `forget` ting an `assume` directive: any functions
  referring to the symbol that `assume` had bound will fail with
  "Symbol not found" errors if executed after the `forget`.

- `freeze directive_id`: fix a directive's current value.

  Freeze removes the directive's random choices from the program
  history and fixes the directive to its current value.  This
  operation is used to gain efficiency for inference strategies in
  the Sequential Monte Carlo style.

- `report directive_id`: report the current value of a directive.

  Report does not re-evaluate the expression or otherwise change the
  program history.

Pseudo-Directives
-----------------

The `force` and `sample` operations are "pseudo-directives" which
have temporary effects on the current program history.

- `force expression = value`: set an expression to a value momentarily.

  Force is a temporary version of `observe` which is immediately
  forgotten after incorporating the observation. This has the effect
  of initializing `expression` to `value` without introducing a
  lasting constraint.  In typical use, the expression is just a single
  variable, which sets that variable to the given value.

- `sample expression`: make a transient prediction.

  Sample is a temporary version of `predict` which is immediately
  forgotten. This has the effect of evaluating `expression` once,
  without adding it to the program trace.  Therefore, unlike
  `predict`, a `sample` d expression will not be maintained during
  inference, and `sample` d expressions will be independent of one
  another (conditioned on the rest of the program history).

Inference
---------

By themselves, the modeling directives do not perform any inference.
When the directives are initially evaluated, their values will be
drawn from the prior, ignoring any observations that have been made.
To move from the prior to the posterior, it is necessary to invoke
some inference operators.

In simple cases, this will just amount to a
transition count and some parameter settings for some generic
inference strategy.  For more complex cases, Venture supports
user-programmable inference that can capture arbitrarily complex
problem-specific insights.  The inference expressions are described
in the :ref:`Inference Syntax Reference <inference-section>`.

Venture inference is also available in a continuous mode:

- `infer loop(expression)`: execute continuous inference.

  The infer loop idiom evaluates an inference expression and starts
  repeatedly executing the specified inference strategy continuously
  in the background. Values can be queried (e.g. with `report`) while
  inference is in progress.  See `loop`.

- `endloop`: stop any ongoing continuous inference.

  endloop is safe to invoke even if continuous
  inference is not running.

Definitions
-----------

- `define symbol = expression`: define a reusable inference subroutine.

  A typical use case would be::

    define frob = proc(a, b) {
      some(inference commmand);
      some(other inference commmand);
      ... };

  whereupon ``frob`` can be invoked like any
  other inference procedure::

    frob(1, 4);

  This is exactly analogous to definitions in other programming
  languages.

  Note: Model program expressions do not see symbols defined in the
  inference program, (and vice versa: inference expressions do not
  see symbols `assume` d in the model program, except via `sample`).

Miscellaneous Instructions
--------------------------

- `load pathname`: execute the given VentureScript program.

  If relative, the path is resolved relative to the current working
  directory.

- `clear`: reset VentureScript to an empty state.

- `list_directives`: print a description of all extant directives.

- `ci_status`: report the status of continuous inference.

  The ci_status command reports whether continuous inference is
  currently running, and if so with what inference program.
