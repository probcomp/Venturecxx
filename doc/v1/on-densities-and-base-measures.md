Background
==========

Random variables are pretty clearly better than measures for defining
the basic semantics of metaprob.  One reason why is their superior
compositionality: given a random variable rx :: R X on a pair type X,
rx can be recovered from the two random variables that are its
projections on the components of X by rx = (fst . rx, snd . rx) [1].
This is not true of the measure that rx induces however -- there is no
way to recover that from the component measures, because they have no
information about latent dependence between the first and second
components.

It is also the case that, taking the source probability space as
fixed, every random variable induces a unique probability measure over
its output space.  That measure can be defined by integration with
respect to the source, or by exact Monte Carlo, which are actually the
same thing.  To wit, for random variable rx mapping a source space
Omega with probability measure mu_0 into a target space X, the
probability measure mu_rx induced by rx is given by

  mu_rx(S \subset X) = mu_0(rx^{-1}(S))
  = expectation of indicator for S over applying rx to draws from mu_0.

Various advantages may be gained from having alternative
representations of such measures.  A more explicit description of such
a measure may be viewed as a specification of the random variable rx.

Specifications may reasonably be conditional.  For example, the
measure induced by a Gaussian random variable depends upon the mean
and standard deviation.  Thus, it is not unreasonable to associate
with the "normal" procedure, which creates fresh such r.v.s from r.v.s
representing the mean and standard deviation, a procedure that
computes the specification (measure) for any values that the mean and
standard deviation may take on.  Thus the specification itself becomes
a random variable; in this instance one that depends on less of w than
the random variable being specified.

Densities
=========

One commonly practiced style of specifying a measure on a sample space
X is as a density function against some (presumably well-understood)
base measure mu_X.  Typical choices of mu_X are counting measure for
discrete sets X and Lebesgue measure for R^n.  In either case, the
usual assumption is that the desired measure mu is absolutely
continuous with respect to mu_X, in which case the density is exactly
the Radon-Nikodym derivative dmu/dmu_X.

In a computational environment, (a computationally effective
representation of) a Radon-Nikodym derivative dmu/dmu_X with respect
to a well-behaved [2] base measure mu_X actually carries more
information than (a computationally effective representation of) the
measure mu alone.  Specifically, the derivative provides the limits

  lim_{S -> {x}} mu(S)/mu_X(S) = (dmu/dmu_X)(x),

which are not necessarily tractable to compute just from evaluating mu
on subsets S with mu_X-size > 0.

Remark: If mu_X is the counting measure, then these limits _are_
tractable to compute from mu: mu_X({x}) = 1 and

  lim_{S -> {x}} mu(S)/mu_X(S) = mu({x}) = (dmu/dmu_X)(x).

Aside: The formal treatment of this that I found is called the
Besicovitch Theorem, and relies on a metric to define the shrinking
sets S as balls of decreasing radius.  Further, the result is
restricted to metric spaces satisfying some covering theorems, but it
is possible that in our setting a metric will always exist and those
conditions will always be met.

Benefits
========

The major benefit of having an effective representation of those
realized limits is being able to work with exact equality constraints
on random variables with continuous sample spaces.

For example, consider a program that defines some random variable x,
and then proclaims

    [observe (normal x 1) 4]

Of course the probability of a Gaussian with mean x and standard
deviation 1 producing exactly 4 is zero, so prima facie this
constraint cannot be used to form a conditional distribution.
However, we can choose to make sense of this by passing to balls
around 4 and taking the limit as their size goes to zero.
The conditional probability (pardon the notation) becomes

    p(x|4) = lim_{r->0} p(x|B_r(4)) / Z_r               (1)
           = lim_{r->0} p(x) mu_{N(x,1)}(B_r(4)) / Z_r  (2)
           = p(x) lim_{r->0} mu_{N(x,1)}(B_r(4)) / Z_r  (3)
                             / mu_{N(x,1)}(B_r(4)) \
           = p(x) lim_{r->0} | ------------------- |    (4)
                             \ Z'_r * mu_L(B_r(4)) /
           = p(x) N(4|x,1) / Z.                         (5)

Here
- (1) is just interpreting our problem as a limit, but note that
  the normalization constant depends on the radius:
    Z_r = \int_X p(x|B_r(4)) dx.
- (2) is conditional probability with a condition whose probability is
  positive.
- (3) is true by non-dependence of p(x) on r.
- (4) is a choice: since the Lebesgue-size of the ball does not depend
  on x, we can buy it from the normalization constant.
- (5) is the definition of the density (with respect to Lebesgue
  measure) of the Gaussian distribution, which I wrote N(4|x,1); and
  the happy accident that Z'_r tends to the positive quantity Z
  (whereas the Z_r tended to zero, because their defining balls
  shrank).

In particular, having those limits computationally realized permits
- rejection sampling against continuous constraints (if the density is
  additionally bounded above)
- computation of M-H acceptance ratios in the presence of continuous
  constraints
- in fact, computation of M-H acceptance ratios in the presence of
  continuous state variables as well (this is where the Jacobian in
  reversible-jump comes in)
- importance sampling against continuous constraints

Problems
========

Nothing in computing with real numbers is ever easy.  Trying to handle
densities in a general way calls for solving several problems:

Base measure agreement
----------------------

In the example above, the base measure against which the density of
the Gaussian is computed is always Lebesgue measure, regardless of the
value of x.  In general, however, the different measures a given
conditional r.v. induces given different values of its parameters may
not all be absolutely continuous with respect to any fixed,
well-behaved base measure.

Consider for example the following stochastic procedure, inspired by
the Indian GPA problem:

(define (gpa talent_bound grade_cutoff)
  (let ((talent (uniform_continuous 0 talent_bound)))
    (if (> talent cutoff)
        cutoff
        talent)))

Taken as a whole, this thing induces a conditional measure on its
output space that places some finite probability on returning exactly
the value of the cutoff, and infinitesimal probability with density
1/bound (wrt Lebesgue) on returning any value between 0 and the
cutoff.  The only measure that dominates these for all values of the
cutoff is counting measure on R, which is not very pleasant, and in
particular loses information needed to compare different bounds at
non-cutoff returned values.

One might describe this problem as being due to the obvious base
measures [3] for the two branches of the IF not agreeing.  If one
tries to patch it by taking their sum as the base measure for the
whole expression, one might describe the resulting trouble as being
due to those sums being different and non-equivalent measures for
different values of the cutoff parameter.

Normalization constant agreement
--------------------------------

All the density-using algorithms mentioned above, namely rejection
sampling, M-H, and importance sampling with resampling (but not
importance sampling for Z estimation) operate only with density
ratios, so can take advantage even of unnormalized densities.  Trying
to do so, however, introduces another problem very analogous to the
base measure problem, namely that the normalization constant needs to
actually cancel across different values of the parameters.

Approaches
==========

There are several distinct criteria on which an approach to the above
problems may be evaluated.  I will try to keep them distinct in my
thinking:
- How natural will the resulting semantics be to the users?
- How easy is it to implement correctly?
- How efficient will the induced computations be without optimization?
- How easy will it be to optimize to "-O1 level" and how fast will
  that be?
- How easy will it be to optimize to "-O2 level" and how fast will
  that be?

Counting Measure FTW
--------------------

Always use counting measure over representable objects, including
floating-point quantities.

Pro: no mucking around with limits or infinitesimals of anything
Pro: no pretending to represent real numbers when we really don't
Con: loses the polite fiction that real numbers provide

Specifically, this proposal renames logDensity to logProbability, and
requires a correct logProbability method to compute the (conditional)
probability of returning exactly that object, be it a floating point
number, or a list thereof, or not.  For a single floating point number
between 1 and 2, those probabilities will be 2^-52 times the density
of the SP, and will thus more or less cancel in "normal situations".
One may view this proposal as doing analysis with infinitesimals,
where the value of the infinitesimal is the local precision available
in floating point.

Subtleties:

- The probability of returning a given object depends on the precision
  of the underlying floating point representation, which we would
  therefore need to be aware of.

- The density of floating point numbers in R actually varies over
  their range, so the probability that a correctly implemented [4]
  uniform distribution returns the float 1e-10 is around 10^8 times
  less than the float 1e-2.

  - This matters at any interval near zero: the lower half of the
    interval will have twice as many floats as the upper.

- Technically, if the underlying distribution's density is not linear,
  the ideal logProbability is not equal to the density at that float
  times some correction that depends only on the local floating point
  density.  However, a one-point approximation to that integral may
  suffice.

  - [I wonder what the conditions are at which the truncation error
    from that approximation matches the roundoff error induced by
    representing the answer as a floating point number itself.]

  - The theoretical win, of course, is that this quantity is in fact
    the value of the distribution's measure on a finite set, which is
    defined more cleanly than the density.  However, most of the
    measures we have are given as cumulative distribution functions,
    and I will not get into the business of subtracting the values of
    such things at arguments separated by one ulp.

- Not clear whether we become obligated to do error propagation
  analysis on all distributions.  What are the chances that the
  Box-Muller transform actually produces the distribution on floats
  that an ideal Gaussian would induce after rounding?  Do we get to
  lie about that in the logProbability method?  Is that any worse than
  log-space rounding error?

- While this does solve the dimensionality-crossing problem, it does
  it in a weird way, which may confuse users.  In particular, the
  Indian GPA situation does favor the American student, but by a
  finite factor, which:
  - varies with where on the number line the problem is posed; and
  - is not even very large, as log scores go.
  On the other hand, this resolution to Indian GPA is expressly fair:
  you said the GPA was the 64-bit float 4.0, so I assumed in the
  absence of further information that GPAs are rounded to 52 bits of
  accuracy, and this is what I got.

- At this point it becomes tempting to treat deterministic continuous
  functions the same way as random ones, with kooky results: The
  distribution on floats induced by
    (* 3 (normal 0 1))
  differs from the ideal implementation [5] of
    (normal 0 3)
  in skipping some [6] floats in its range, namely those that do not
  divide evenly (among floats!) by 3.  The Jacobian of the
  transformation (* 3) shows up here as an estimate of the rate of
  floats skipped (or multi-hit for a contracting transformation).
  - For a nonlinear transformation, this estimate will of course be
    subject to some truncation error, but it may again be dwarfed by
    the roundoff error incurred by computing the Jacobian in floating
    point.

- The above tells me that a really faithful rendition of "I give you
  the probability of getting exactly this float" either sucks to
  implement or is not possible.  Of course, a somewhat unfaithful
  rendition may be acceptable, despite the cognitive dissonance of
  treating floats exactly in one place and fuzzily in others.  I
  wonder whether there is a coherent interface which says "I give you
  the (approximate) probability of getting exactly this float assuming
  no numerical error", that is, all previous computations being done
  exactly and rounding just the one time at the end.  That seems nasty
  too, because now the answer to the Indian GPA example above seems to
  depend on whether the cutoff parameter was computed by an integer or
  floating-point process (which, however, is known from its type tag).

Type-Driven Universal Base Measure
----------------------------------

Basic idea: the base measure which all densities must be against is
determined by the type of the datum, with Lebesgue measure for all
representations of real numbers, counting measure for discrete
objects, measure product for product types, and disjoint union of
measures for sum types.

The above base measure actually has two versions, which correspond to
static and dynamic typing.  The sample space in the dynamic typing
version is a huge disjoint union over all possible type tags (which
may grow during execution if users are allowed to define their own
record types).  Technically, this requires the logDensity method of
any SP to accept any object, and return -inf if that SP actually
cannot return that object (for example, if the object has the wrong
dynamic type).

- An ill-typed logDensity query could arise if inference tries to
  change some piece of control flow that causes some constraint to
  backpropagate to a new operator that emits objects of a different
  type.  Returning -inf amounts to rejecting the transition.

The static typing version reduces the sample space to be only those
objects that are permitted by the static type of the variable.  On
the one hand, this permits densities to assume well-typed query
objects; but on the other hand, the tag-checking remains, because now
the constructors (or the union injection functions more generally)
have to do it.

- I do not think the static typing version requires any additional
  programming support for representing the base measures induced by
  the static types, beyond the type checker it needs anyway.

Issues:

- The conditional measures of many objects will not be absolutely
  continuous with respect to Lebesgue measure, and thus will not have
  well-defined densities.  Notable examples:
  - All deterministic floating-point functions.
  - In particular, the "float" function that changes the type of an
    integer to floating point, and thus changes the base measure from
    counting to Lebesgue.
  - Floating-point literals (which can be viewed as applications of
    the "float" function to a notional exact representation of the
    literal).
  - Categorical with continuous inputs.
  - All SPs some of whose control paths look like the above, notably
    including the gpa SP from before.
  - Note: "Density undefined" is worse than "Density [wrt counting
    measure] 0 everywhere except this one place", which is how
    deterministic functions (including continous ones) behave now.

- What should the base measure be for function-valued variables?
  Candidate styles:
  - Defunctionalization measure, namely "every closure body is a type
    tag, and the environment is a big product type of everything in
    it".
    - Sub-choice: treat the entire accessible lexical environment or
      just the part that the body actually refers to?  How to deal
      with eval, get-current-environment, and that crew?
  - Intentional measure, which must be some horrible disaster
    involving horrible subsets of horrible infinite-dimensional
    function spaces.  How big is this blob of functions?
    - Hilbert spaces are a possible avenue of attack.

- In either case, how should one write the density methods of SPs that
  return functions?  Examples:
  - Categorical with functional inputs
    - This is basically a bug in Venture currently
  - Foreign uncollapsed foo
    - This currently assumes that the query value will always be an SP
      of the class returned by the maker, which breaks down in the
      "change of control flow" case that plagues dynamically typed log
      densities in general.
  - Do we want to open the "identity of procedures" can of worms?

- For the sanity of the users, we will want to detect the case where a
  floating-point SP is observed to give an integer answer, e.g.
    [observe (normal x 1) 2]   instead of   [observe (normal x 1) 2.0]
  Even though this is technically valid, with probability 0, it is
  very likely to be a programmer error, especially among beginners.
  - Alternately, we could decree that the integer gets automatically
    converted to a float in this circumstance.  Haven't thought
    through the ramifications of this plan.

Issues particular to the statically typed version:

- We will probably want to back-propagate constraints through
  constructors (or union injection functions generally).

- How elaborate will the static type system be, and what are
  appropriate base measures for various interestingly-typed beasts
  like universally and existentially quantified polymorphic things?
  Are those all essentially like function types?

- Type checking could be postponed until it is known that inference is
  to be applied, thus permitting e.g. forward simulation even from
  models that violate the type system.  In this case, some care should
  be taken with particle weights, because resampling does make base
  measure compatibility assumptions about the particles.

Implicit Unconditional Per-SP Base Measure
------------------------------------------

This is what Venture tries to do now.  Base measures are assumed to be
determined by the SP, but are not explicitly represented anywhere.
Further, they are effectively required to be fixed for each SP that
has a logDensity method, and may not vary with the inputs.  To the
extent that this is so, the correction factors cancel and things just
work out.

Issues:

- What should happen if a proposal changes control flow paths such
  that the operator SP of some node, and therefore maybe the base
  measure, change?  If the base measures are implicit, there is no way
  to distinguish changing from normal to gamma from changing from
  normal to poisson.

  - If memory serves, Venture unconditionally resimulates actual
    application forms whose operators change, even when that is not
    necessary.  However, values that are removed from such by no
    stronger a guard than an invertible identity (e.g., the return
    value of the if in the gpa procedure) may absorb, which leads to
    ridiculous problems.

- What about (in the hopefully not too distant future) compounds with
  density annotations?  Does any change in the environment trigger a
  change in the implicit base measure, or only changes in the body?
  What if the base measure of a closed-over variable changes?  What if
  that variable is actually the return value, or controls the base
  measure thereof?  What if a change in the environment leads to a
  change of control flow in the body of an application?

  - This is one of the places where I got stuck in the v1-scm
    prototype.

- What should the implicit base measure for the above gpa procedure
  be, if it is to be packaged as a foreign SP?  Remember that only
  counting measure dominates the simulator's measure for all values of
  the cutoff parameter.  Do we rule out being able to provide a
  density for gpa at all?  If so, how do we detect violations of that
  rule?

Explicit Base Measure
---------------------

Represent the base measure explicitly.  Every SP gets a baseMeasure
method which returns an instance of a BaseMeasure class which has
whatever behavior we want.  Sub-choice: does the baseMeasure method
get to read the arguments or not?

One obvious behavior would be computing various relationships between
measures:
- is that measure absolutely continuous with respect to me?
- what is the density of that measure with respect to me at this
  point?

One minimalist implementation of this strategy would be to build in
only counting measure, Lebesgue measure, and product (and union?)
measures; and perhaps expose an API to allow the user to define new
primitive ones.

Many of the currently built in SPs will then explicitly have measures
that are the same ones they would always have under the "Type-Driven
Universal Base Measure" proposal, but for example categorical can
claim counting measure (with support on its inputs) regardless of the
types of the objects it is selecting among.

Issues:

- M-H and co will presumably need to be adjusted to check base measure
  compatibility when computing density ratios.
  - Does this require per-variable alignment between detach and regen,
    or is there a notion of "total" that works?
  - For example, if two DRG nodes switch base measures in opposite
    directions, e.g. one from Lebesgue to counting measure while
    another from counting to Lebesgue measure, is just adding up their
    density numbers ok, or do we need to abort the transition because
    of base measure mismatch?
  - The answer seems to be different for brush.
  - What about brush that "spills" out, like the return value of an if
    whose branches have different base measures?  Is that just back to
    being drg now?  But presumably the base measure of the if itself,
    conditioned on the values of its branches, is just counting
    measure; or do reversible identities not work that way?

- What, still, is the base measure of the gpa procedure?  If it can
  vary with the input arguments, it now becomes feasible to have it be
  Lebesgue + an atom at the cutoff.  However, two such things for
  different cutoffs are not even absolutely continuous either way,
  never mind equal, so how do we compare densities with respect to
  them?
  - Just bar all such transitions?
  - Introduce machinery for computing base-measure-change corrections
    at points where the density exists locally?

- Efficiency:
  - What will these base measure objects cost at runtime?
  - Is it possible to check base measure compatibility once per a given
    piece of source code and rely on it repeatedly for many proposals?
    - Presumably this will be easier if the baseMeasure methods cannot
      read the arguments.
    - Certainly, MCMC schemes that are implemented in practice do not
      often carry explicit representations of base measures around at
      runtime.
    - On the other hand, if the baseMeasure method is an unknown
      function that can read the arguments to the procedure, there is
      no general way to predict its outcome.
      - This can be mitigated by inlining the baseMeasure methods of
        known SPs; are dead code elimination and constant folding
        sufficient to eliminate the base measures at runtime?

Represent the Full Radon-Nikodym Decomposition
----------------------------------------------

This option is complementary to any of the above proposals that
involve Lebesgue base measures.  This option permits more sampler
measures to be treated as having Lebesgue base measure, so likely
benefits the less flexible base measure proposals (Universal
Type-Driver and Implicit per-SP) disproportionately more.

Theorem [Radon-Nikodym Decomposition]: If mu and nu are sigma-finite
nonnegative measures on a sigma-algebra B [which probability measures
are], then nu can be decomposed in a unique way as nu = nu_a + nu_s
where

- nu_a is absolutely continuous with respect to mu;
- nu_s is singular with respect to nu, i.e. there is a set A of
  mu-measure zero such that nu_s(X\A)=0.

In other words, the measure of a sampler can always be represented as
a density plus a piece that is mu-almost-everywhere zero.

Unfortunately, that extra piece is not in general guaranteed to be a
sum of finite-size Dirac deltas at a finite (or even countable) set of
points.  The encyclopediaofmath.org reference provides a
counter-example made out of the Cantor set.  The example can be
realized computationally if an SP is permitted to return an infinite
string of bits represented lazily.  In this case it's easy to write a
procedure that samples an exact point from the Cantor set uniformly at
random; the measure of which is not absolutely continuous with respect
to Lebesgue measure, and yet still assigns zero probability to any
given point of R.

That said, we may be able to get considerable mileage out of a
broader, if perhaps still incomplete, representation of the singular
component of the decomposition than const 0.

For instance, we may restrict the singular component to being
finite-size Dirac deltas only.  This can be represented by an optional
SP method named logSpikeHeight.

- Note: spikes only apply to base measures for which the measure of a
  single point is 0, e.g. Lebesgue but not counting measure.  The
  handling of spikes should take this into account.

- In M-H, spikes always beat densities, but if both sides of a
  proposal are either spikes or densities, then dividing them gives
  the correct acceptance ratio.
  - Spikes may also be unnormalized; same considerations apply as
    always.
  - In this case, I think node alignment is not needed.  That is, the
    corrections that apply to a proposal that moves one node from
    spike to density and another from density to spike probably cancel
    out, permitting the normal acceptance ratio computation to proceed
    (I have not checked this).

- For rejection, upper bounds are computed spike-major.

- For importance sampling with resampling, particle weights can
  probably get away with being the total of spikes and the count and
  total of densities (will #spikes + #densities always equal the
  constant number of observations?), with particles always chosen from
  those that have the fewest densities (most spikes) but otherwise by
  weight.

- Notice that if logSpikeHeight is not -inf, the logDensity is
  irrelevant.

- This is actually doing analysis with infinitesimals, where the count
  of densities is the power of infinitesimal one has.  Compare the
  "Counting Measure FTW" proposal, where all three numbers are folded
  into one, by giving the infinitesimal a finite size (namely the
  local density of floating point numbers, which in 64-bit floating
  point is 2^-52 between 1 and 2).

- It may be useful to also offer an optional enumerateSpikes method,
  by analogy with the present enumerate for discrete distributions.

- In this representation, the conditional measure of "float" has a
  spike of log height 0 at its argument, and furthermore "float" is
  invertible (for known input type; and of course the inverse will be
  partial in general).

Issues:

- This proposal does not actually solve the base measure selection
  problem, just makes Lebesgue measure palatable as an answer for more
  samplers.  (In the absence of samplers returning infinite objects,
  does the above representation actually cover all samplers over R?)

- Some analytical care is needed with product measures.  How should we
  represent the measure mu of a sampler that returns a pair of real
  numbers, one of which is either 4.3 or 5.2 and the other is
  Gaussian?  Suppose for a minute that the base measure is to be
  Lebesgue measure on R^2.  mu is by no means absolutely continuous
  wrt Lebesgue^2, and in fact the Radon-Nikodym derivative is the zero
  function.  On the other hand, mu has no atoms, either, so the exact
  representation proposed above does not cover it.
  - It may be tempting to address this by permitting per-component
    choice of density vs spike, but that does not cover the needs of
    samplers that produce curves in the output space, such as
      (lambda () (let ((x (normal 0 1))) (pair x (sin x))))
    (viewed as a primitive)

- Efficiency:
  - Is the cost of asking everything about spikes, which most things
    will not have, tolerable?
  - How easy is it to either fast-path that out, or get rid of it by
    inlining and dead code elimination?

Approaches for Normalization Constants
======================================

Venture's current approach to normalization constants is analogous to
the "Implicit Unconditional Per-SP Base Measure" proposal, with much
the same issues.  It would be possible to institute the thing that's
analogous to the "Explicit Base Measure" proposal, with much the same
issues.  Note that this choice is essentially independent of the base
measure choice.  It's harder to treat the normalization constant as a
type, because it's actually a number (if an unknown number).

General Issues
==============

Looking the list over now, the maxim "Treat base measure
incompatibility as a type error in application of that inference
program to that model" does not uniquely select a solution to the base
measure problem, though it was very helpful for formulating the
options.

The density bound of an expression (as distinct from a procedure
application) is the maximum density bound over all SPs that could flow
to operator position.
- This is computable if the SP is not being changed by the scaffold
- This is computable if the SP is changing but in a sufficiently
  controlled way, e.g. only elements of the closure, or only some
  polite latent variable in an uncollapsed foreign model.
- How do we deal with/take advantage of this information?

Density of what?  In all the above, I have ignored the question of
which variables a given density method is taken to integrate out.  One
possible story is to say that densities apply at the PSP level,
integrating out everything inside the PSP but being conditioned on the
values of all the requests the PSP reads to compute its answer
(including LSRs).
- This suggests a distinction between LSRs and internal randomness in
  a PSP: the density integrates internal randomness out, but
  conditions on the values of LSRs.
- Is that distinction actually safe?  That is, in the presence of
  different kinds of metadata, would there be any circumstances where
  some variable wants to be integrated out for one purpose but kept
  for another?  Do we have a coherent story for permitting such
  multiple views?
- Are LSRs equivalent to trampolining through returned procedures?
  - Or do they constrain the applications thereof enough to be different?
    - Are they like let, then?

In the MCMC literature, deterministic proposals are different from
stochastic ones because determinants of Jacobians start to appear.  Do
we need to carry that information around with our (conditionally)
deterministic procedures?  This is particularly relevant to the
"Represent the Full Radon-Nikodym Decomposition" proposal, but
possibly to the others as well.  Or is there a reason this is not
needed?  Is there a capability we could gain by making a place for the
Jacobian (or its determinant) in the SP interface?

Reactions to Reversible-Jump MCMC
=================================

These reactions are to the exposition at
http://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=2&ved=0CCoQFjAB&url=http%3A%2F%2Fwww.ece.duke.edu%2F~lcarin%2Frjmcmc_20090613.pdf&ei=UgCHVcztLpCWyATn6IPgDQ&usg=AFQjCNH-92Pj2qJ7D4qpX2misdEc_zdF_w&sig2=opYeKFReuyet1NInfA3A8g&bvm=bv.96339352,d.aWw

Hm.  He assumes a likelihood function.  Is it true that the
density/base measure/compatibility problem has to be solved at the
observations in order to even provide a cogent one?

Hm.  M-H can be justified in terms of integrals over sets in the state
space of the Markov chain.  The Jacobians ultimately come from there
(changes of variables to reduce to integrating over the same space).

Evaluation of Venture MH:
- The discrete object "k" can index control flow histories, and the
  continuous parameters can be the values of all continuous variables
  that occur.
- This is obvious if all nodes contain either discrete or
  fixed-dimension objects only, and never change type.
- There may be validity constraints on the continuous variables,
  e.g. compatibility between the inputs to a comparison operation and
  the control flow choice made as a consequence of its output.
- It may be appropriate to (notionally) include in k all control flow
  choices that occur inside foreign SPs, thus accounting for changes
  of type that their outputs may experience as executions vary.
  - Including as control flow varying the "closure bodies" of returned
    procedures.
- There is a wrinkle, in that computation of the index k and the
  parameter vector is interleaved; but that's actually probably ok
  (haven't checked the details).
- One way to view the story of Venture resimulation M-H is, in my
  reference's notation:
  - x  is the present state
  - u  is the randomness sampled by regen from the SPs it calls
  - x' is the proposed state
  - u' is the rhoDB, namely the randomness regen would have to sample
    to get back from x' to x
  - regen computes g(u) as it goes, and the preceding detach computes
    g'(u') (up to mucking around with DeltaLKernels).
  In this framing, h : (x,u) -> (x',u') is a permutation, and thus has
  Jacobian determinant 1.
  - bug: a deterministic DeltaLKernel (which Venture does not rule
    out!)  has no channel by which to report its Jacobian determinant.

Notes
=====

[1] Really rx = liftM2 (,) (fst . rx) (snd . rx) but we're all friends
here.

[2] We will return to the topic of choosing well-behaved base
measures, but for now it suffices to think of them like porn: you'll
know one when you see it.

[3] For fixed parameter values, the obvious base measure for the
cutoff variable is counting measure, and for talent Lebesgue.

[4] Correctness in this sense clearly means "Sample a floating point
number with the distribution induced by (notionally) sampling an exact
real according to the distribution being modeled and then rounding it
to the operating precision."  There is a subtlety here: do we fix a
specific rounding mode (such as "toward 0" or "to nearest"), or do we
respect the processor rounding mode that obtains in the dynamic
context of the call?  This choice of course (slightly) affects the
probability of returning any given float that logProbability should
report.

[5] Which we do not have!  Except by running Box-Muller in higher
precision and then rounding.

[6] How many?  You might think two of every 3, but that's not right
because the source floats are denser than the target floats.  I expect
it to either hit 2 out of 3 or 4 out of 3 (i.e., hitting some twice)
depending on how much denser the source is, which is to say on the
first bit of the mantissa.  Not obvious at the moment whether this
correction from 3 will arise naturally from the general handling of
float density discussed earlier.

References
==========

http://www.encyclopediaofmath.org/index.php/Absolutely_continuous_measures
https://en.wikipedia.org/wiki/Absolute_continuity#Absolute_continuity_of_measures
https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_theorem
http://www.encyclopediaofmath.org/index.php/Differentiation_of_measures

