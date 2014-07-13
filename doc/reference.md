Venture Language Reference
==========================

Usage
-----

Venture can be invoked in multiple styles: in the interactive console, and as a Python library.

Interactive console:

    $ venture
    >>> assume x (normal 0 1)
    >>> observe (normal x 1) true

Python library:

    from venture.shortcuts import *
    v = make_church_prime_ripl()
    v.assume("x", "(normal 0 1)")
    v.observe("(normal x 1)", "true")

Python library (batch use):

    from venture.shortcuts import *
    v = make_church_prime_ripl()
    v.execute_program("""
        [assume x (normal 0 1)]
        [observe (normal x 1) true]
    """)

There are also multiple syntaxes for expressions: Venchurch (Scheme/Church-like) and VentureScript (Javascript-like). This document will use the Venchurch syntax.

Instructions
------------

Venture programs consist of a series of instructions which are executed by the Venture SIVM (Stochastic Inference Virtual Machine). Venture supports the following instructions:

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

Directives
----------

The `assume`, `observe`, and `predict` instructions, also called *directives*, make up the core modeling language of Venture. Each directive contains a modeling expression to be evaluated. At any time, the probabilistic execution trace consists of all directives that have been evaluated and not forgotten.

`[assume symbol expression]` declares a variable, binding the result of `expression` to `symbol` in the global environment.

`[observe expression value]` conditions on observed data, constraining the result of `expression` to be equal to `value`.

(Note: Currently, an expression can only be constrained by an `observe` directive if its outermost procedure application is the result of a stochastic computation, rather than a deterministic one. For example, `[observe (normal 0 1) 0]` is valid, but `[observe (+ 1 (normal 0 1)) 0]` is not because `+` is a deterministic function of its arguments.)

`[predict expression]` tracks an `expression`, allowing its value to be reported before or after inference.

(Note: A `predict` instruction is persistent, in the sense that it becomes part of the program trace and will be maintained and potentially resampled during inference. A `predict`ed expression may affect the evaluation of later expressions that are correlated or conditionally dependent. To evaluate an expression non-persistently, use `sample`.)

In addition to the directives themselves, there are instructions `forget`, `freeze`, and `report` which manipulate directives.

`[forget directive_id]` removes a directive from the program trace, so that further inference will behave as if it had never been executed.

`[freeze directive_id]` fixes a directive's current value, removing its random choices from the program trace. This instruction is used to implement Sequential Monte Carlo inference strategies.

`[report directive_id]` reports the current value of a directive, without re-evaluating the expression or otherwise changing the program trace.

Pseudo-Directives
-----------------

The `force` and `sample` instructions are "pseudo-directives" which have temporary effects on the current program trace.

`[force expression value]` is a temporary version of `observe` which is immediately forgotten after incorporating the observation. This has the effect of initializing `expression` to `value` without introducing a lasting constraint.

`[sample expression]` is a temporary version of `predict` which is immediately forgotten. This has the effect of evaluating `expression` once, without adding it to the program trace. Therefore, unlike `predict`, a `sample` instruction will not be maintained during inference, and `sample`d expressions will be independent of one another (conditioned on the rest of the trace).

Inference Instructions
----------------------

By themselves, the modeling directives do not perform any inference: when the directives are initially evaluated, their values will be drawn from the prior, ignoring any observations that have been made. Venture provides two "modes" of inference: manual (with the `infer` instruction) and continuous (with `start_continuous_inference` and `stop_continuous_inference`).

Both `infer` and `start_continuous_inference` take an *inference expression*, which is an expression that specifies what inference strategy and what parameters (e.g. number of iterations) to use. The types of inference expressions are described below.

`[infer expression]` evaluates an inference expression and executes the specified inference strategy on the current program trace for the specified number of iterations.

`[start_continuous_inference expression]` evaluates an inference expression and starts executing the specified inference strategy continuously in the background. Values can be queried (e.g. with `report`) while inference is in progress.

`[stop_continuous_inference]`, when called after `start_continuous_inference`, stops the continuous inference process.

`[continuous_inference_status]` reports the status of continuous inference: whether it is running and with what parameters.

Miscellaneous Instructions
--------------------------

`[clear]` clears away the current program trace and all directives, starting from a clean slate.

`[get_global_logscore]` returns the sum of the log probability density of each random choice in the current program trace. TODO caveats

`[get_logscore directive_id]` returns the log probability density of the outermost random choice made during the evaluation of the specified directive. TODO caveats

`[rollback]` TODO

Modeling Expressions
--------------------

TODO

Inference Expressions
---------------------

TODO
