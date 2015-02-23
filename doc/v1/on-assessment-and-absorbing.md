On Assessment and Absorbing
---------------------------

The usual case
==============

Consider first the usual case.  Let f be a stochastic procedure from
the set Args to the set Out, representing a family p_f of conditional
distributions over Out.

  f : Args -> Out; p_f

For args in Args, out in Out, we can run f:

  simulate f args ~ p_f(out|args)

For f to be called _assessable_, we must also be able to compute

  assess f out args = log(p_f(out|args)) + C

where the probability is given with respect to a measure on Out that
does not depend on out or args and dominates all the p_f(.|args).  We
allow assessment to be un-normalized with implicit normalization
constant C independent on args [TODO: Can C vary with out?].

If f is assessable, we can evaluate the relevant factor in the
acceptance ratio of an MH proposal that changes args but does not
change out:

  assess f out args' - assess f out args

If in addition we can compute an upper bound on possible values of
assess f out, varying any args that are not constant, we can form the
relevant factor of the acceptance probability for a rejection sampler
for the posterior on args conditioned on out:

  assess f out args' - bound f out <constant args>

These two abilities are called _absorbing_.

Compositions
============

Now take f to be a composition involving an intermediate state drawn
from the set X:

  p_f(out|args) = \int_x p_f^jt (out,x|args)

The joint can always be written as

  p_f^jt(out,x|args) = p_f^x(x|args) * p_f^o(out|x,args)

and this is particularly natural when f is a let form: "let x = f^x
args in f^out x args".

Simulation still works:

  simulate f args = let x = simulate f^x args
                     in simulate f^out (x:args)

but assessment loses:

  assess f out args = log[\int_x e^(assess f^x x args) * e^(assess f^out out (x:args))] = :(

However, if f^out is assessable, we can still condition on the output
of f (absorb at f) in an MH proposal:

- extend the proposal by adding
  x' = simulate f^x args'
- include in the acceptance ratio the term
  assess f^o out (x':args') - assess f^o out (x:args)

and, if f^out has a bound (which needs to vary x if x is not a
deterministic function of the args that are held constant), we can
still condition on the output of f (absorb at f) in a rejection
sampler:

  assess f^out out (x':args') - bound f^out <constant args U x>

Naturally, this works recursively on f^out.

Tail-assessability
==================

Motivated by the above, define a function f to be _tail-assessable_ if either
- f is assessable, or
- f factors as above and f^out is tail-assessable.

The previous discussion proves that tail-assessability is conserved by
pre-composition with simulable (not necessarily assessable) functions,
without changing the measure or the normalization constant.

To deal with compositional languages, let us also define our notions
for expressions.  For convenience, we take our expressions to be in
A-normal form (i.e., all intermediates explicitly named).

Define an expression e in environment sigma to be _assessable with
respect to variables v_i_ iff the function defined by evaluating
(lambda (... v_i ...) e) in sigma is assessable.  (Note that I expect
that the v_i in this lambda expression may shadow some bindings that
sigma may have for v_i.)  Define e in sigma to be _tail-assessable wrt
variables v_i_ analogously.

What are the recursive rules of (tail-)assessability?

- A constant or a variable lookup are not usefully assessable, being
  deterministic.

- A lambda expression by definition produces a (tail-)assessable
  procedure iff its body is (tail-)assessable with respect to the
  formal parameters of the lambda.

- A let expression preserves tail-assessability of its body regardless
  of its bound expression, but in general destroys assessability of
  its body.  Variables that appear free only in the bound expression
  may be freely included in the tail-assessable set of the let, as may
  the bound variable (because it is no longer free in the let
  expression at all).

- A trace-in form technically preserves (tail-)assessability of its
  body, but connotes that automatic assessor computations should not
  cross its boundary.

- A definition is like a let (whose body is the rest of the scope
  after the definition).
  - TODO Assessability of recursive definitions?

- An if form is best thought of through Church encoding of booleans,
  and deferring evaluation of the branches.

- A begin form preserves (tail-)assessability of its tail expression,
  except that TODO I haven't thought about side-effects yet.

- The other operatives are either deterministic or macros.

- Application (in A-normal form) taken with respect to the variables
  holding the arguments preserves (tail-)assessability of the
  procedure applied.  Application is not in general (tail-)assessable
  wrt the variable holding the operator, but some changes to the
  operator may nonetheless admit absorption, depending on the base
  measures and normalization constants.  Some cases may be deducible
  for compound procedures, based on what closed-over variables the
  operator's body is assessable with respect to.

The above rules permit automatically computing tail-assessors for a
potentially respectable number of compound procedures, though by
themselves they do not yet deal with proposals that change the
contents of closures (as an uncollapsed exchangeable sequence would).
But that could perhaps be handled by broadening the operator
compatibility critera.

Note: on this view, the identity function and the selector function
are not usefully assessable, as they are deterministic.  However,
(tail-)assessability is preserved under composition with deterministic
invertible functions (though in general the normalization constant and
the base measure on the output space may depend on the invertible
function in question).

Generalization
==============

There is no a priori reason to restrict the proposal that a
tail-assessable function makes to its intermediate state x to being
from the prior.  We could permit f to extend an M-H proposal by adding

  x' ~ q(x'|out,x,args')

for arbitrary proposal distribution q, provided the ability to compute
the acceptance ratio term

     [  p_f^out(out|x',args') * q(x|out,x',args)  * p_f^x(x'|args')  ]
 log [ ------------------------------------------------------------- ]
     [   p_f^out(out|x,args)  * q(x'|out,x,args') *  p_f^x(x|args)   ]

(using whatever cancellation between p_f and q was desirable).  This
could be valuable if q is closer to p(x|out,args) than the prior.

An analogous generalization applies to rejection.

More
====

There are two other pieces of this story, namely:

- If x is stochastic, we can propose only to x, without changing args; and

- If f_x is (tail-)assessable, we can propose to args leaving x fixed.

In fact, is it not the case that resimulation M-H and rejection both
rely on the whole model being tail-assessable on the observations?

Is giving foreign procedures the ability to expose tail-assessability
structure what LSRs in Venture v0.2 are all about?

Claim: For LDA (and every other standard statistical model we care
about) we just know what the decomposition into f^x and f^out is.
- So, can we take any additional advantage of this decomposition?
