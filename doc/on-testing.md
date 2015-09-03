Correctness-Testing Probabilistic Programs
==========================================

This document concerns itself with the question "Did I implement my
model and inference correctly?".

By way of clearing the context, I will mention several kinds of other
questions one might want to answer when testing a probabilistic
program.  This document is *not* about any of these questions:

- Did I push my time-accuracy tradeoffs far enough?

  - Variant: Did my Markov chain converge?

  - Variant: Do I have enough samples?

  - Variant: Do I have enough effective sample size (drawing
    repeatedly from a few long chains)?

  - Apparently there is a robust literature of convergence
    diagnostics, but I have not yet studied it.

- Is this a good Markov chain for this model?  (That is, can it be
  made to converge faster?)

  - This is in a sense a performance question.

- Was this a good model to begin with?

  - Cross-validation (including the PSIS trick in that Gelman paper)

  - WAIC

Another note: testing and debugging are two different things.  For
testing, you want as narrow an information pipe as possible, flowing
from as broad a segment of your program as possible, to gain
confidence that there are no problems in a broad range of
circumstances, and to quickly focus attention on circumstances where
there are problems.  For debugging, you want as thick an information
pipe as possible, to understand where the problem you are looking for
may be hiding.  But, of course, you also want to focus that thick pipe
to source from the actual problem area, to avoid being overwhelmed by
information.  This document is not about debugging strategies either.

Regimes
-------

Probabilistic programming admits a variety of operating regimes, which
seem to call for different testing strategies.

- Testing **deterministic answers**: Some probabilistic programs are
  actually deterministic, and have predictable answers.  Traditional
  testing is a good fit here.

  - Just run the program and check the answer

- Testing **universal invariants**: For any program, there are
  situations that should never happen (for example, type errors).
  Traditional testing is a good fit here, too.

  - Just run the program and check the invariant.

  - If the program is random, may help to run several times with
    variable and recoverable initial entropy.

- Testing **almost-everywhere invariants**: Some things happen in a
  model "with probability zero".  These cannot be treated as errors
  the same way as universal invariants -- see [Musings on the
  Impossible](https://github.com/mit-probabilistic-computing-project/Venturecxx/blob/master/doc/impossibility.md).

- Testing **exact equality in distribution**: In the simplest
  nontrivial case, one knows the exact probability distribution on
  outputs that should obtain.  The tests that are applicable classify
  by the characterizations of the two putatively equal distributions
  that are available, or that one wishes to compare, and by the
  dimension of the output space:

  - exact measure vs exact measure

    - Should always agree on every query -- this is a universal
      invariant.

  - exact sampler vs exact measure

    - 0-D (discrete) output: one-sample Chi^2 test.

    - 1-D output: one-sample K-S test.

    - more-D output: When do you ever have an exact measure in high
      dimensions?  Project and/or bin down to 1-D or 0-D if the
      measure permits.

  - exact sampler vs exact sampler

    - 0-D (discrete) output: two-sample Chi^2 test.

    - 1-D output: two-sample K-S test.

    - more-D output: project to various independent 1-D tests and/or
      bin to various independent 0-D tests (as many and as varied as
      desired).

      - TODO Is there anything better?

  - exact density vs exact density

    - Should always agree on every query -- this is a universal
      invariant.

  - exact sampler vs exact density

    - In 0-D the density is a measure: one-sample Chi^2 test.

    - 1-D: Compute the cumulative distribution function by quadrature
      and one-sample K-S test.

    - more-D: TODO ???

  - These tests are valid at ~every sample size, but drawing more
    samples increases their strength.

  - Can plug this in to a traditional test framework by thresholding
    the p-value.

  - an exact tail-assessable representation (see [Approximating K-L
    Divergence]
    (https://github.com/mit-probabilistic-computing-project/Venturecxx/blob/master/doc/on-approximating-kl-divergence.md))
    behaves like an exact fully-assessable representation for an
    approximate distribution.  See the next item.

- Testing **approximate equality in distribution** is where I no
  longer know good decision procedures.  By "approxmate" I
  specifically mean "there is a parameter N such that sending it to
  infinity makes the equality exact", though I admit multiple
  dimensions of approximation (i.e., multiple parameters such that
  some nested limit is exact.

  - sampler+density vs density

    - small 0-D: Compute K-L divergence by enumeration.

    - 1-D or low-D: Compute K-L divergence by quadrature.

    - large 0-D or high-D: Compute K-L divergence by Monte Carlo
      integration.

  - Test is asymptotic in

    - The number of samples used to estimate the K-L, if Monte Carlo.

    - The parameters of approximation of the distributions (e.g., the
      number of samples used to estimate full assessment from tail
      assessment).

  - The best "decision procedure" I know so far is to eye-ball the
    results of multiple runs with various parameters and see whether
    they are zero or not.

  - One good trick: Calibrate errors in the K-L divergence by
    evaluating it for two different approximations of the same
    distribution.  That is, if testing whether K-L between A_n and B_m
    converges to zero, calibrate by comparing different realizations
    of A_n.

Examples of Exact Distribution Equality
---------------------------------------

- Testing **probabilistic primitives**.  The various methods of an SP
  are different representations of purportedly the same probability
  distribution, so cross-check them.

  - log densities of counts methods may be comparable to versions of the
    same SP that do not attempt to maintain sufficient statistics, for
    example on the inferences they produce.

- Testing **distribution identities**, for example that

    N(N(mu, var1), var2) = N(mu, var1 + var2).

  Such identities give an additional way to cross-check various
  methods of the primitives used to implement those distributions.
  The Gaussian example above can be tested sampler-vs-sampler to gain
  confidence in the Gaussian sampler, or tail-assessor vs assessor
  to gain confidence in sampler-assessor agreement.

  - One class of identities is the behavior of location and scale
    parameters, for SPs that have such.  These tests can detect
    mis-parameterization bugs.

  - Another class of identities arises when some object (like a
    BayesDB population model) purports to be able to compute
    conditioned variants of a distribution.  Then equalities like

      p(x'|z)/p(x|z) =  p(x',z)/p(x,z)

    for all x', x, z become relevant.

  - Distributions like Student-T that are defined as compositions can
    be (partially) tested by comparing their definition as a
    tail-assessable process to their purported direct assessor.

    - Actually can compute the K-L in both directions, which hits two
      distinct code paths.

  - The sampler for a distribution that is a conjugate prior can be
    tested by comparing a posterior computed by rejection sampling to
    one computed by the collapsed version of the model.

  - Rejection sampling results can be compared exactly against
    analytic solutions.

- The **Geweke identity** from [1]:

  - given p(x), p(d|x), and stationary T_d: x -> x', the chain

    ```
    x_n+1 ~ T_{d_n}
    d_n+1 ~ p(.|x_n+1)
    ```

    should be stationary on the joint distribution p(x,d).  Can compare
    any iterate, or any sub-collection of a long run, against repeated
    forward simulation from p(x,d).

  - In practice, the distributions involved tend to be only
    tail-assessable, so are well-treated as instances of approximate
    equality in distribution.

Examples of Approximate Distribution Equality
---------------------------------------------

- Testing transition operators that converge to a **known exact
  posterior**: All too often, the precise intended action of a
  transition operator is not characterized well enough to serve as a
  useful test.  If the operator's intended target distribution
  (typically the posterior) is known, one can fall back on testing
  that iterating the operator converges to it.

  - Can do K-L as above on any derived distribution (e.g., latents,
    predictive).

    - Nice property: the true K-L must monotonically decrease under
      iteration of the operator; if the fidelity of the K-L
      approximation is good compared to the speed of reduction, that
      can be used without having to iterate the operator very many
      times.

    - The test is asymptotic in

      - The number of samples used to estimate the K-L

      - The number of samples used to estimate full assessment from
        tail assessment

      - The number of iterations of the transition operator

  - Alternately, can take "many" iterates of the operator, hoping for
    it to have converged, and treat it as exact equality in
    distribution (i.e., use Chi^2 or K-S on 0-D or 1-D projections of
    the result).  This is somewhat risky, because it's hard to detect
    convergence in general, but could be a reasonable test of
    inference algorithms with convergence heuristics

- One can similarly approach a **computable exact posterior**: If some
  instances of the problem are tractable to an exact method like
  rejection sampling, at least the predictive distribution will be
  tail-assessable, and one can compute K-L convergence.

- Testing **different approximations to the same distribution**:

  - Is it true that K-L between two approximations converges to zero?
    If so, I can use K-L as above, as both are likely to be
    tail-assessable.

- Testing by **asymptotic certainty**: Even if the posterior of a
  given instance of a problem is not characterizable, one can fall
  back to asymptotic certainty to create tests.

  _Asymptotic certainty_ is the following property of Bayesian models:
  If the supplied data are IID according to some distribution Q, then,
  as the number of data points increases:

  - If Q is in the model's hypothesis class, the posterior predictive of
    the model converges to Q.

  - If not, the posterior predictive converges to that distribution in
    the hypothesis space whose K-L divergence from Q is minimum.

  - TODO: Is the convergence known to be monotonic in K-L?

  As a consequence of this,

  - Can do K-L as above on the predictive distribution

    - I would typically expect to be able to invent
      in-hypothesis-space test distributions by forward sampling (any
      prefix of) the latents from the model, holding them fixed and
      generating data by repeated forward sampling from the rest.

    - The test is asymptotic in:

      - The number of samples used to estimate the K-L

      - The number of samples used to estimate full assessment from
        tail assessment

      - The number of iterations of the transition operator

      - The number of data points used for training

TODO
----

- Where does: Cook, Gelman, Rubin 2006, Validation of Software for
  Bayesian Models Using Posterior Quantiles
  http://www.stat.cmu.edu/~acthomas/724/Cook.pdf
  fit in?

- There is a testing mechanism proposed in Roger Grosse's PhD
  dissertation.  I recall thinking it was very complicated, but it may
  be worth perusing again.

- vkm suggested that there are ways to distinguish three cases:

  - A coding bug

  - A non-convergent Markov chain

  - A convergent Markov chain that didn't run long enough

- Is it possible to detect convergence-slowing bugs in a transition
  operator that don't impact the distribution it converges to?  Are
  there such things?

- Note: the above assumes normalized assessments.  If the assessments
  or tail assessments are up to a normalizing constant, the K-L
  measures will be off.

  - Is that situation salvageable?

References
----------

[1] J. Geweke. Getting it right: joint distribution tests of posterior
simulators. JASA, 2004.
http://qed.econ.queensu.ca/pub/faculty/ferrall/quant/papers/04_04_29_geweke.pdf

See also Roger Grosse
https://hips.seas.harvard.edu/blog/2013/06/10/testing-mcmc-code-part-2-integration-tests/
for a more intuitive introduction.
