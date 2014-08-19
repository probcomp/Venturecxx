NOTES ON V1PRE
==============

(From Vikash's point of view 7/7/2014, edited lightly by Alexey
8/14/2014)

To clearly illustrate the power (rather than merely suggest the
elegance) of v1pre, I need to be able to:

(i) build models that have primitives defined in terms of inference

(ii) control inference using values that inference modifies

Here an example of (i):

[ASSUME infer-param (mem (lambda (val prior_var)
  [ASSUME theta (normal 0 prior_var)]
  [OBSERVE (normal theta 0.1) val]
  [INFER (mh default one 10)]
  theta))]
[ASSUME variance_used (gamma 1 1)]
[OBSERVE (normal [infer-param 10 variance_used] 0.5) 10]
[PREDICT variance_used]

N.B. [infer-param 10] is "apply with external trace"; for now, that
means we treat the procedure as likelihood free.

Here is an example of (ii):

[ASSUME is_trick (bernoulli 0.1)]
[ASSUME weight (if is_trick (uniform_continuous 0 1) 0.5)]

[ASSUME add_data_and_predict (lambda ()
   [OBSERVE (bernoulli weight) True]
   [INFER (mh default one 10)])]

[ASSUME find_trick (lambda ()
  (if (not is_trick)
      (begin (add_data_and_predict) (find_trick))))]
(find_trick)

Note: Not [PREDICT (find_trick)].  Are bare expressions implicitly inference programs? -- Ed

In an ideal world (which this very probably is not!), I would also be
able to illustrate how (rather than just assert that) it is possible
to implement something like MH as a library procedure. This requires
something like mu and is most likely puntable.

Anyhow, here are some notes on lambda/mu:

(lambda <formal args> <body-exp>) => current CSP; likelihood-free if
applied with [], otherwise if applied with () generates an internal
trace and absorbs at it

This is a procedural-only procedure: all you specify is how to
simulate something.

(mu <CSP: args to val> <CSP: ( args , val ) to log weight>) => SP,
with marginal probability. If applied with [], generates no trace and
absorbs using the weight CSP. If applied with (), generates a trace,
and absorbs at it, both for the simulator and the weight
calculator. Note that typically the value of this will just be to
reuse old computation, but propagation will go through instances where
the weight is used in regen/detach. Other cases deferrable for now.

This is a procedural-declarative procedure: you specify both how to
simulate, and also have the ability to answer (certain) declarative
questions about the procedure's behavior.

There are many questions. I can send you some notes on how to expand
out something like MH later on (I don't have the full story yet but I
have some key elements). But right now as it seems unlikely I'll hold
off until you ask.
