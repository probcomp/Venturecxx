Ways of Testing Probabilistic Programs
--------------------------------------

Probabilistic programming admits a variety of operating regimes, which
seem to call for different testing strategies.

- Testing **deterministic answers**: Some probabilistic programs are
  actually deterministic, and have predictable answers.  Traditional
  testing is a good fit here.

  - Just run the program and check the answer

- Testing **unversal invariants**: For any program, there are
  situations that should never happen (for example, type errors).
  Traditional testing is a good fit here, too.

  - Just run the program and check the invariant.

  - If the program is random, may help to run several times with
    variable and recoverable initial entropy.

- Testing **almost-everywhere invariants**: Some things happen in a
  model "with probability zero".  These cannot be treated as errors
  the same way as universal invariants -- see [Musings on the
  Impossible](https://github.com/mit-probabilistic-computing-project/Venturecxx/blob/master/doc/impossibility.md).

- Testing **known exact answer distributions**: In the simplest
  nontrivial case, one knows the exact probability distribution on
  outputs that should obtain.

  - If the expected distribution is discrete or 1-D can use Chi^2 or
    K-S (one or two sample).

    - Sampling from the expected and test distributions is sufficient;
      can also use the measure of either or both

    - Test is valid at ~every sample size, but drawing more samples
      increases its strength

    - Can plug this in to a traditional test framework by thresholding
      the p-value.

  - Can compute approximate K-L and check that it approaches 0 as the
    fidelity of the approximation improves.

    - Works for any tail-assessable (preferably full-assessable)
      expected and tested distributions (see [Approximating K-L Divergence](https://github.com/mit-probabilistic-computing-project/Venturecxx/blob/master/doc/on-approximating-kl-divergence.md))

    - Test is asymptotic in

      - The number of samples used to estimate the K-L

      - The number of samples used to estimate full assessment from
        tail assessment, if applicable

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
    it to have converged, and use Chi^2 or K-S on the result (if it's
    discrete or 1-D).  This is somewhat risky, because it's hard to
    detect convergence in general.

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

Testing Probabilistic Primitives
--------------------------------

There is a slightly different problem facing attempts to test
primitives, because here the subject of the test is whether two (or
more) different descriptions of the same (usually well-understood)
distribution agree.

- The typical example would be agreement between the sampler and
  assessor for a Venture SP.

  - For discrete SPs, can compare the simulator to the log density with
    Chi^2.

  - For 1-D SPs, can compare the simulator to the log density with K-S,
    computing the CDF by quadrature.

    - May be necessary to ensure the quadrature is successful.

  - For more dimensions, can always try various (or random)
    projections

  - TODO Is there any story for full-coverage comparisons of
    simulators and assessors for multi-dimensional distributions?

- In special cases, it may be possible to use some identities to gain
  confidence.  For example:

  - The Gaussian distribution can be tested by comparing the K-L of
    the tail-assessable representation

    `normal 0 1 >>= \mu -> normal mu 1`

    to the analytic answer `normal 0 (sqrt 2)`

  - Distributions like Student-T that are defined as compositions can
    be (partially) tested by comparing their definition as a
    tail-assessable process to their purported direct assessor.

    - Actually can compute the K-L in both directions, which hits two
      distinct code paths.

  - The sampler for a distribution that is a conjugate prior can be
    tested by comparing a posterior computed by rejection sampling to
    one computed by the collapsed version of the model.

- log densities of counts methods may be comparable to versions of the
  same SP that do not attempt to maintain sufficient statistics, for
  example on the inferences they produce.

TODO
----

- Geweke-style testing?

- vkm suggested that there are ways to distinguish three cases:

  - A coding bug

  - A non-convergent Markov chain

  - A convergent Markov chain that didn't run long enough

- Is it possible to detect convergence-slowing bugs in a transition
  operator that don't impact the distribution it converges to?  Are
  there such things?

- Note: the above assumes exact assessments.  If the assessments or
  tail assessments are up to a normalizing constant, the K-L measures
  will be off.

  - Is that situation salvageable?
