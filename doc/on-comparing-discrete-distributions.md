Comparing Discrete Distributions
================================

How shall one compare two discrete distributions?  If one has exact
assessors for both, it suffices to enumerate the sample space and
check that the assessments are all equal.  But what if one or both are
available only as opaque samplers, or, in the more usual setting,
finite drawn samples?

Pearson Chi Square
------------------

The usual suggestion is to perform a one-sample or two-sample Chi^2
test.  The most usual one-sample Chi^2 test is specifically Pearson's
Chi^2:

1. Compute
     \hat chi^2 = sum_i (O_i - E_i)^2/E_i
   where O_i is the number of occurrences of outcome i observed
         E_i is the number of occurrences of outcome i expected

2. If the sample is drawn from the expected distribution, \hat chi^2
   will approximately be distributed according to the chi^2
   distribution with n-1 degrees of freedom, where n is the number of
   possible outcomes i.

3. If the expected distribution is computed from the data with a
   maximum likelihood fit from a k-parameter family, it is considered
   appropriate to reduce the number of degrees of freedom by k when
   asking "does the data come from some distribution in this family?".

Two-sample Chi^2 for testing whether two given samples are plausibly
drawn from the same (unknown) underlying distribution is derived as a
one-sample Chi^2 against a parametric family.  To wit: Given samples
s_1 and s_2 from sample space S, the disjoint union of s_1 and s_2 is
taken to be a sample from some distribution on {1,2} x S, and the
question is posed as "Is it plausible that this union came from a
distribution where the S-value is independent of the source label?".

Said independence assumption corresponds to an |S|-parameter family of
distributions: |S|-1 parameters for the frequencies of the various
S-values (the -1 is due to the requirement of normalization), plus 1
parameter for the frequency of 1 as opposed to 2 labels.  The
two-sample Chi^2 test then consists of

1. (trivially) computing the maximum likelihood such distribution, and

2. Performing the one-sample Chi^2 test against it, while

3. Correcting the number of degrees of freedom by |S|.

G-test
------

While debugging an implementation of Chi^2, I found the idea of G-tests
discussed on Wikipedia: https://en.wikipedia.org/wiki/G-test.  The proposed
test statistic is

    G = 2 sum_i O_i ln (O_i/E_i)
  where O_i, E_i as above.

This is apparently also approximately distributed as the chi^2
distribution, with the same number of degrees of freedom as the Chi^2
test above.  Wikipedia says

 "For very small samples the multinomial test for goodness of fit, and
  Fisher's exact test for contingency tables, or even Bayesian
  hypothesis selection are preferable to the G-test.[citation needed]"

The rationale given for preferring G over Chi^2 is that \hat chi^2 is
actually an approximation for G that drops terms of third order in
(O_i - E_i)/E_i; which is appropriate if the observations are close to
the predictions, but degrades if they are not (or, presumably, if the
predicted values are small).

Exact Test
----------

It is also possible to compute an exact test: just sum the probability
of every configuration at least as improbable as the given one.  This
is of course intractable for large numbers of categories and
observations.  Both the G statistic above and the chi^2 statistic are
alleged to be approximations to it, and various corrections to them
are alleged to be better approximations.

There are actually two plausible versions of this for the parametric
family situation:

a) Fit a member of the family from the original sample and measure
   the likelihood of other possible samples in that member, or

b) For each possible sample, measure the likelihood of that sample
   coming from the member that best fits it.

TODO What, actually, are the distributions of the test statistic that
obtain in situations (a) or (b) in the parametric family phrasing of
this test?

Kolmogorov-Smirnoff
-------------------

The K-S test statistic can be computed for any discrete distribution,
provided we have an ordering on the possible outcomes (and, ideally,
an efficient cumulative distribution function).  People don't like
using it for distributions whose CDFs have steps for some reason; does
the theorem characterizing its behavior fail?

There is, methinks, a way to make it work even if so: Expand the state
space from S to S x [0,1], ordered lexicographically.  Interpret the
theoretical distribution as being uniform on the augmented intervals;
now the mass is zero at every point.

This suggests at least two different possible tests:

a) Augment the sample by choosing random values from [0,1] for each
   point; then compare the resulting empirical cdf against the
   theoretical one by the standard K-S test.

b) Construct a quasi-empirical cdf by interpreting the sample as
   implying a piecewise-linear cdf that passes through the expected
   points at the endpoints of the intervals and is linear within each
   one.

Permutation Test
----------------

TODO describe the family of permutation tests

Axch Test
---------

TODO I assume this has been invented before; what is it called?

Given a fixed target distribution, it is possible to estimate the
results of the exact test directly, without enumerating all possible
samples.  To wit, choose any test statistic (such as the chi^2), then
draw N samples of size n from the known distribution and compute that
test statistic for all of them, and measure the ordinal position of
the query sample in that list.  If the sample was drawn from the
hypothesized distribution, the ordinal should be distributed uniformly
between 0 and N.

The issue with this test is that it scales linearly with the original
sample size and with the desired test precision.  It is
computationally favorable for small n, if at all.

TODO Is there a coherent variant for goodness of fit to a parametric
family?  I anticipate some of the same difficulties as for the exact
test.

Structure
---------

Chi^2 and G are tests of goodness of fit to a parametric family, which

- can be used as tests of independence by choosing the family to be
  "products of all marginal distributions", and

- can be used as two-sample tests of equidistribution by testing for
  the independence of the sample membership label.

K-S is a test of goodness of fit to a fixed distribution, which

- has a variant that is a test of equality directly

- TODO Is there a variant of K-S for testing goodness of fit to a
  parametric family?

The exact test and the axch test are tests of goodness of fit to a
fixed distribution, which

- have an unchecked candidate variant that is a test of goodness of fit
  to a parametric family, which

- could then be used as a test of independence or a two-sample test of
  equidistribution as above

The permutation test is directly a test of independence, which

- can be used as a two-sample test of equidistribution.

Issues
------

- Presumably, the G-test and the exact test can be generalized to the
  two-sample question the same way standard chi^2 is.

- Is it true that the G test is the same as the likelihood ratio test
  (for the hypothesis class "any multinomial")?
  - This seems to be suggested by https://en.wikipedia.org/wiki/Multinomial_test

- The G statistic appears to be 2N times the K-L divergence of the
  theoretical distribution from the observed one (N is the total
  number of samples).
  - Does that matter?  Does K-L have a useful interpretation that
    would help with using it for equality testing this way?
  - Are there good conditions under which the chi^2 distribution
    permits interpretation of the K-L divergence?

- What is this Wilks's Theorem that claims to determine (limiting)
  distributions for all likelihood ratio test statistics?
  - https://en.wikipedia.org/wiki/Likelihood-ratio_test

- Is there a good justification for the likelihood ratio testing
  structure, which seems to be "compare against the max-likelihood
  distribution from some parametric family"?  Should we instead have a
  prior on the parameter space and integrate?

- Does the K-S test actually work for CDFs with finite steps?

- What, if any, is the relationship between the K-S applied to a
  discrete distribution (possibly with the state space augmented as
  above) and any of the other goodness of fit tests discussed above?

- What, if any, is the relationship between two-sample K-S and
  constructing a distribution equality test from one-sample K-S by
  fitting an independent multinomial as above?  Do K-S tests even make
  sense for distributions obtained as fits from a parametric family?

- What, if any, consistency properties should we expect under the
  operations of coarsening the bins or restricting attention to a
  subset of bins?

- Should we move to the G test, or some more elaborate procedure that
  involves computing exact probabilities sometimes, for testing
  sameness of discrete distributions in the Venture test suite?  The
  motivation would be reducing mis-tests caused by mis-application
  of chi^2, e.g. to situations where it is not a good approximation.
  - The test of recovering the geometric distribution comes to mind.
  - Could empirically assess whether the chi^2 stat computed for a
    sample drawn from the geometric distribution (or a power law or a
    poisson) actually is chi^2 distributed (with how many degrees of
    freedom?)
