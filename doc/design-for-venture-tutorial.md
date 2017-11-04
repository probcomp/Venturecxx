Date: Summer 2015
Status: The tutorial that existed between 2015 and 2017 was inspired
by some of these thoughts

Candidate outline with gaps, 6/10/15
------------------------------------

Intro

- Intro normal-normal model (one data point)
  - x ~ Normal(0,1)
    y ~ Normal(x,1)
    What is p(x|y=2)?
  - Normal is a decent model for general unimodal distributions: the
    mean is the "answer" and the variance is the "uncertainty".
    - Except: Gaussians have very thin tails, so they really model "I
      basically know the answer, I'm just a bit unsure".
  - One major misconception that will come from studying the
    univariate Gaussian is that in 1-D one can solve problems with
    quadrature, but that gets exponentially bad with more dimensions.
    - A symptom of this is that the K-S test works in one dimension.
- Relevant analytical/philosophical properties
  - for all distributions, summing samples sums means and variances
  - scaling a sample scales the mean and the standard deviation
    - corollary: averaging iid samples preserves the mean and
      decreases the standard deviation quadratically slowly
  - if the mean and variance are finite, the shape of the distribution
    of the sum tends toward Gaussian
  - the Gaussian is the maximum entropy distribution with fixed mean
    and variance (TODO: What is the corresponding characterization of
    multivariate Gaussians?)
    - philosophy: mean and variance are the exact two conserved
      quantities of summing samples (which is convolution of density
      functions).  It eventually erases all other information, if the
      mean and variance are finite.
  - for Gaussians in particular, conditioning sums the precisions and
    moves the mean to the precision-weighted average
- Wolog, can assume the prior is a standard normal (by shifting and
  scaling)

Basics

- Implement standard algorithm templates instantiated on this problem
- For each method:
  - characterize the computational properties of the Gaussian
    distribution needed to do the method
  - characterize the performance of the algorithm as a function of the
    mean and precision of the observation, and any algorithm
    parameters
  - "performance" means compute resources and inference quality, or
    rather the tradeoff space between them
    - compute resources are the usual latency, memory, and total work
      (= latency if not parallelizable)
    - inference quality for a sampler is how close (e.g. in K-L
      divergence) its distribution is to the target
    - aside: a randomized procedure for estimating an integral over a
      probability distribution (such as the numerical probability of
      some event) is also a sampler, but one whose objective is the
      delta function at the right answer.  Here K-L divergence is not
      a useful quality measure; one must resort to distances in answer
      space.  We do not deal with this query type in this tutorial.
- Rejection sampling, proposing from the prior
  - loop: candidate ~ N(0,1) ; The prior on x
          accept = p(y=2|x=candidate) / max_x* p(y=2|x=x*) ; x* = 2
          if flip(accept): return candidate
          else: loop
  - Theorem: this loop returns an exact sample from the posterior
  - Requires a likelihood density bound as an additional
    computational element.
  - If the bound is not tight, still correct, but slower.
- Rejection sampling with an arbitrary proposal distribution
  - General case requires densities for the posterior and the
    proposal, and a bound on the ratio
    - A hypothetical independent "universal rejection proposal object"
      would need a *lower* bound on its density, which seems
      farfetched for samplable distributions with infinite support.
    - So some special relationship knowledge seems to always be
      needed.
  - Special cases exploit cancellations
    - e.g., sample from the likelihood and reject at the prior, if the
      likelihood is amenable.
  - Note: sampling from the analytic posterior (and knowing that one
    is sampling from the analytic posterior!) can be seen as a
    rejection sampler that always accepts
  - Using a Gaussian proposal as a proxy for the general case, explore
    the nature and causes of performance variation as the proposal
    varies from "too broad" to "too narrow and in the wrong place" to
    "too narrow despite being in the right place"
  - Extra credit: Compare a fatter-tailed proposal distribution than a
    Gaussian, e.g. Cauchy.
- Importance sampling with resampling, from the prior
  - parameter: n = number of trials
    candidate_i ~ N(0,1) for 0 <= i < n ; The prior on x
    weight_i = p(y=2|x=candidate_i)
    return (select candidate_i with probability proportional to weight_i)
  - Theorem: As n -> infty, the distribution on return values of this
    procedure approaches the exact posterior
  - Aside: if used for integration, could weight instead of
    resampling; this is called "likelihood weighting".
  - Characterize performance as a function of the number of trials.
  - N.B.: The resampling can be done online.
- Importance sampling with resampling, from an arbitrary proposal
  distribution
  - Again, cancellations
  - Again, explore causes of performance variation with changing a
    Gaussian proposal.  Compare rejection sampling.
  - Note: for finite particle count, resampling always introduces
    approximation error.  TODO What exactly does rejection's exactness
    guarantee cost?  Needing a bound; performance effect; anything
    else?
- Special case with cancellation: Rejection sampling from the
  likelihood (since it is samplable in this case); prior weighting
  from the likelihood
- Resimulation M-H from the prior
  - x_0 ~ N(0,1)
    proposal_t ~ N(0,1)
    alpha_t ~ max(1, p(y=2|proposal_t) / p(y=2|x_t)) ; Much cancellation
    x_t+1 = if flip(alpha_t): proposal_t else: x_t
  - Theorem: at t -> infty, x_t tends, in distribution, to the posterior
  - Cancellation in the acceptance ratio
  - Characterize distribution (and performance) as a function of the
    number of proposals
  - Characterize convergence as a function of the mean and stddev of
    the observation
  - Note: M-H acceptance criterion is not the only one, but is the
    fastest that (provably?) conserves detailed balance.  Accepting
    independently less often is correct too, just slower.
- Arbitrary simulation kernel M-H
  - General case of prior-independent kernels requires density of the
    kernel and the prior, but there may be cancellations in special
    cases
  - Characterize intermediate distributions, performance, convergence
    as a function of parameters and trial count for a Gaussian
    proposal kernel
- Arbitrary delta kernel M-H
  - General case requires density of the kernel and the prior
  - Special case of symmetric kernels cancels kernel density
  - Characterize intermediate distributions, performance, convergence
    as a function of parameter and trial count for a Gaussian drift
    proposal kernel
- TODO Relationship between importance sampling with online resampling
  and prior resimulation M-H.  Different acceptance rules?
- TODO Relationship between same with a general proposal distribution?

Sufficient statistics, exchangeable coupling, collapsing

- As the number of data points increases from 1, what happens?
  - Semantically equivalent to 1 data point with an appropriately
    modified mean and variance
  - Can capture that idea with a (make_suff_stat_normal mu) that
    absorbs changes to mu without traversing all the applications
    - count, sum, sumsq are certainly enough; perhaps effective mean
      and effective precision are also enough
  - This looks like a new computational element: logDensityOfData,
    etc.
    - TODO Spell out what the sufficient statistics actually are and
      how to actually compute the logDensityOfData for normal.
  - In Venture, this is (currently) captured with the rather messy
    AAALKernel thing
  - Aside: There's also (make_suff_stat_normal mu sigma) and
    (make_suff_stat_normal sigma); and I suppose also a
    (make_suff_stat_normal), but I don't know how to use that one.
    - TODO Work out the variations
- The analytic solution can actually also be captured computationally
  (which can still be relevant if, e.g., the prior mean is subject to
  inference).
  - One version is using the counts to make proposals to the variable
    from the exact local posterior
  - Another version is collapsing the variable out entirely: use the
    counts and the parameters of the prior as the representation of
    the local posterior on that variable, and perform computational
    operations with respect to it directly
    - logDensityOfData can be reused to absorbing changes to prior
      parameters (without traversing all the applications)
    - the counts can be used to sample from the predictive
      distribution directly
    - which adjusts the counts, changing the distribution on the next
      application.  This leads to an exchangeable sequence implemented
      with mutation.
- Exchangeability: A sequence of random variables is called
  "exchangeable" if all permutations have the same probability
  (density).
  - Fact (TODO is this a citable theorem? de Finetti?): Exchangeable
    sequences are exactly the possible sequences of random results of
    a thunk that may be referring to immutable but unknown random
    state (not iid because observing one output gives information
    about the unknown state, and therefore the other outputs, but
    exchangeable because the order of reads of the unknown state
    cannot matter).
  - Theorem [de Finetti]: Exchangeable sequences are also exactly the
    possible sequences of results of a thunk endowed with power of
    Abelian mutation.
    - Defn. of Abelian mutation: the state being mutated admits an
      action of an Abelian group G, and there is a function f from the
      output space into G, such that the mutation attendant on
      emitting x is application of f(x) to the state.
    - TODO Is the initial value of the state permitted to be random?
    - TODO Does the state have to be (isomorphic to) one such group?
      If so, does it have to start at the identity?
  - collapsed_beta_bernoulli is an example of this in Venture; we do
    not have an adequate stock of collapsed Gaussians (but see cmvn).

Auxiliary variable methods

- Now we can do auxiliary variable methods, one manifestation of which
  is as proposal distributions that have latent randomness and can
  only report density conditioned on it.
  - Example: propose (normal (normal mu_prior sig_1) sig_2), where
    sig_1**2 + sig_2**2 = sig_prior**2, but you don't allow yourself
    to know that.
  - TODO Analysis justifying this proposal and what the acceptance
    ratio is
    - TODO(vkm): Is there more than one analysis?  Persistent vs
      transient auxiliary variable?
  - Characterize the performance of this as a function of sig_1 and
    sig_2.  Is it always better for sig_2 to be bigger (i.e., to be
    able to integrate out more of the proposal)?
  - TODO(vkm) Apply Hongyi's multi-particle trick to this.
    Multi-particle estimates of something?  Explain.
- General auxiliary variable analysis
  - TODO What is it?  Are there different ones?
  - TODO Is there a general pattern of differences between expanding
    the state space of the Markov chain with a persistent auxiliary
    variable, vs creating and destroying the variable transiently, as
    part of a "move"?
  - TODO What are the proof obligations for an aux-var thing to be
    sound?  What is needed to discharge them automatically?
- Various canned fancy nonsense can be analyzed as an instance of this
  auxiliary variable framework
  - characterize performance relationship of parameters of method vs
    parameters of data point
  - Slice sampling
  - HMC
  - TODO How does particle Gibbs apply to this problem (maybe in the
    multi-data scenario)?  How is particle Gibbs an instance of an
    auxiliary variable method?  Is traditional SMC such a thing too?
    - What are the performance differences between collapsing two data
      points into one with suffstats and importance sampling, vs
      SMC/particle Gibbs over the two data points?  As a function of
      the order and their means and precisions?

Unaddressed topics

- There's maximization (e.g. gradient-based) which is a whole other
  kettle of non-Bayesian (Fisherian?) fish.

- Decomposition into coherent inference sub-problems.
  - Is this an instance of the aux-var trick also, with the subproblem
    identifier being the auxiliary variable?  Where does the
    correction come from?  p(u|x)?

- Foreign stochastic procedures

Draft list of computational elements
------------------------------------

One goal is to accumulate a list of computational elements
- simulator
- assessor (density evaluator)
- stats maintenance (incorporate/unincorporate, or homomorphism to
  Abelian group element, possibly with a separate set that is acted
  upon)
- bulk assessor (all applications at once, via stats)
- simulator with weight (proposal not from the prior)
  - this is also a simulation kernel with cancellation against the prior
  - one might imagine supporting improper priors like this
- simulator with weight against the prior and applications
  - this is also a simulation kernel with cancellation against the local posterior
  - uncollapsed AAA Gibbs kernels are instances of this
- detached delta kernel
  - In the simple case, a thing with a simulator and an assessor
  - Hongyi has been working out a less simple case
- derivatives of simulator, assessor, and bulk assessor (for posterior
  gradient methods)
  - interactions thereof with weighted simulators? posterior-weighted
    simulators?
- reverse simulator (for proposing from the likelihood without any
  dependence on the prior)
  - one might imagine doing inference against improper priors like
    this
- bulk reverse simulator

General vague idea: Pay when connecting edges
---------------------------------------------

General vague idea: building structure is more or less free; can add
values to it; when connecting edges, have to pay -- either in the
distribution on the value that completes the edge or in weight
generated thereby.

Aside: quasirandom sequences
----------------------------

Aside: I expect there to be a perfectly good definition of quasirandom
sets/sequences [1] for arbitrary measures (probability distributions).
If generating them composes the way sampling composes, and in
particular if something like Markov chains work in that setting, these
stand to be much better for computing integrals than sequences of
independently random samples.  Is there a justification of the
"subsample a long chain" style of integration on these grounds?  (I
actually expect not, except perhaps by coincidence on some example.)

[1] http://en.wikipedia.org/wiki/Low-discrepancy_sequence
