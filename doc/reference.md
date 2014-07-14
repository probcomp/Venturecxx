Venture Reference Manual
========================

Usage
-----

Venture can be invoked in two styles: in the interactive console, and
as a Python library.

Interactive console:

    $ venture
    >>> assume x (normal 0 1)
    >>> observe (normal x 1) true

Python library:

    from venture.shortcuts import *
    v = make_church_prime_ripl()
    v.assume("x", "(normal 0 1)")
    v.observe("(normal x 1)", "true")

Python library (batch invocation):

    from venture.shortcuts import *
    v = make_church_prime_ripl()
    v.execute_program("""
        [assume x (normal 0 1)]
        [observe (normal x 1) true]
    """)

There are also two syntaxes for expressions: Venchurch
(Scheme/Church-like) and VentureScript (Javascript-like). This
document will use the Venchurch syntax.

Overview
--------

Venture programs consist of a series of instructions which are
executed by the Venture SIVM (Stochastic Inference Virtual
Machine).  These instructions

- Build up a generative model for some phenomenon of interest
  (`assume`),

- Include events on which that model is to be conditioned (`observe`),

- Specify queries against that model (`predict`),

- Invoke inference to explore the space of explanations of the events
  that the model judges as plausible (`infer`), and

- Preform various additional and supporting functions (the others).

The "meaning" of a Venture program is the (joint) distribution on
model variables and predictions that executing the program induces.
The major instructions affect the meaning as follows:

- `assume` and `predict` extend the state space of the
  distribution with additional variables or predictions, respectively.
  The marginal of the extended distribution with respect to the
  previously extant variables and predictions remains unchanged.

- `observe` records an event as having occurred, but *does not alter
  the current distribution*.  Instead, `observe` sets up an **implicit
  conditional** distribution.  The implicit conditional is obtained
  from the distribution given by all `assume`s and `predict`s,
  ignoring `infer`s, by conditioning on all `observe`s.  The implicit
  conditional only affects the meaning of a Venture program through
  the invocation of `infer` instructions.

- `infer` mutates the distribution by executing the inference program
  given to it.  Typical inference programs move the distribution
  nearer (in KL-divergence) to the implicit conditional given by all
  executed `observe`s.  For example, `[infer (mh default one 100)]`
  mutates the distribution by taking 100 steps of a certain standard
  Markov chain, whose stationary distribution is the implicit
  conditional given by the preceding `assume`s, `predict`s, and
  `observe`s.

For a more extensive conceptual introduction to Venture, see the
[draft Venture paper](http://arxiv.org/abs/1404.0099).

Instruction Reference
---------------------

Summary:

    [assume symbol expression]
    [observe expression value]
    [predict expression]
    [configure options]
    [forget directive_id]
    [freeze directive_id]
    [report directive_id]
    [infer expression]
    [start_continuous_inference expression]
    [stop_continuous_inference]
    [continuous_inference_status]
    [clear]
    [rollback]
    [get_logscore directive_id]
    [get_global_logscore]

    [list_directives]
    [get_directive directive_id]
    [force expression value]
    [sample expression]
    [get_current_exception]
    [get_state]
    [reset]

### Directives

The `assume`, `observe`, and `predict` instructions, also called
*directives*, make up the core modeling language of Venture. Each
directive contains a modeling expression to be evaluated. At any time,
the probabilistic execution trace consists of all directives that have
been evaluated and not forgotten.  Venture maintains an index of
unique identifiers for directives so they can be referred to by other
instructions.

- `[assume symbol expression]`: declare and initialize a variable.

  Assume evaluates the `expression` and binds the result to `symbol`
  in the global environment.

- `[observe expression value]`: condition on observed data.

  The condition constrains the result of `expression` to be equal to
  `value`.

  An expression can only be constrained by an `observe` directive if
  its outermost procedure application is the result of a stochastic
  computation, rather than a deterministic one. For example, `[observe
  (normal 0 1) 0]` is valid, but `[observe (+ 1 (normal 0 1)) 0]` is
  not, because `+` is a deterministic function of its arguments.

  `observe` has no effect on the distribution of values obtained by
  running the Venture program until the next time `infer` is invoked.

- `[predict expression]`: register a persitent prediction.

  Predict tracks the `expression`, allowing its value to be reported
  before or after inference.

  A `predict` instruction is persistent, in the sense that it becomes
  part of the program history and will be maintained and potentially
  resampled during inference.  A `predict`ed expression may affect the
  evaluation of later expressions that are correlated or conditionally
  dependent.  To evaluate an expression non-persistently, use `sample`.

### Directive manipulation instructions

In addition to the directives themselves, there are instructions
`forget`, `freeze`, and `report` which manipulate directives.

- `[forget directive_id]`: remove a directive from the program history.

  Further inference will behave as if that directive had never been
  executed.

  Be careful `forget`ting an `assume` directive: any functions
  referring to the symbol that `assume` had bound will fail with
  "Symbol not found" errors if executed after the `forget`.

- `[freeze directive_id]`: fix a directive's current value.

  Freeze removes the directive's random choices from the program
  history and fixes the directive to its current value.  This
  instruction is used to gain efficiency for inference strategies in
  the Sequential Monte Carlo style.

- `[report directive_id]`: report the current value of a directive.

  Report does not re-evaluate the expression or otherwise change the
  program history.

### Pseudo-Directives

The `force` and `sample` instructions are "pseudo-directives" which
have temporary effects on the current program history.

- `[force expression value]`: set an expression to a value momentarily.

  Force is a temporary version of `observe` which is immediately
  forgotten after incorporating the observation. This has the effect
  of initializing `expression` to `value` without introducing a
  lasting constraint.  In typical use, the expression is just a single
  variable, which sets that variable to the given value.

- `[sample expression]`: make a transient prediction.

  Sample is a temporary version of `predict` which is immediately
  forgotten. This has the effect of evaluating `expression` once,
  without adding it to the program trace.  Therefore, unlike
  `predict`, a `sample` instruction will not be maintained during
  inference, and `sample`d expressions will be independent of one
  another (conditioned on the rest of the program history).

### Inference Instructions

By themselves, the modeling directives do not perform any inference:
when the directives are initially evaluated, their values will be
drawn from the prior, ignoring any observations that have been
made. Venture provides two "modes" of inference: manual (with the
`infer` instruction) and continuous (with `start_continuous_inference`
and `stop_continuous_inference`).

Both `infer` and `start_continuous_inference` take an *inference
expression*, which is an expression that specifies what inference
strategy and what parameters (e.g. number of iterations) to use. The
types of inference expressions are described below.

`[infer expression]` evaluates an inference expression and executes
the specified inference strategy on the current program trace for the
specified number of iterations.

`[start_continuous_inference expression]` evaluates an inference
expression and starts executing the specified inference strategy
continuously in the background. Values can be queried (e.g. with
`report`) while inference is in progress.

`[stop_continuous_inference]`, when called after
`start_continuous_inference`, stops the continuous inference process.

`[continuous_inference_status]` reports the status of continuous
inference: whether it is running and with what parameters.

### Miscellaneous Instructions

`[clear]` clears away the current program trace and all directives,
starting from a clean slate.

`[get_global_logscore]` returns the sum of the log probability density
of each random choice in the current program trace. TODO caveats

`[get_logscore directive_id]` returns the log probability density of
the outermost random choice made during the evaluation of the
specified directive. TODO caveats

`[rollback]` TODO

Modeling Expressions
--------------------

TODO

Inference Expressions
---------------------

TODO
