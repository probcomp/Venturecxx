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
