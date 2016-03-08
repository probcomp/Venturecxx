Abstract
--------

Through 3/8/16, we had a recurring problem with the semantics of the
method then named `logDensityOfCounts`.  This document lays out the
cause of confusion, the decision to specify that `logDensityOfCounts`
returns the probability of one data sequence (not the sufficient
statistic), the decision to rename `logDensityOfCounts` to
`logDensityOfData`, and the rationales.

Context
-------

Consider a sequence of applications of some SP.  Structurally, think
common parameters theta shared between multiple calls to a thunk:

```
(let ((theta ...))
  (lambda () (... theta ...)))
```

Suppose those applications produced values x_i.  We are interested in
log p(x_i|theta), ideally without having to gather x_i from the trace
and explicitly sum the individual log densities.

Suppose the thunk's output's dependence on theta factors through some
sufficient statistic T.  That is, for t = T(x_i),

  p(x_i|theta) = p(x_i|t) p(t|theta)

where p(x_i|t) is (for any given data set x_i) a constant that does
not depend on theta.

The incorporate and unincorporate methods of the appropriate SP object
can be arranged to maintain the appropriate value of t.  The issue is
how to define what the `logDensityOfCounts` method should return,
because there are two sensible candidates: log p(x_i|theta) or log
p(t|theta).

Cause of Confusion
------------------

The confusion arises because

- The effective spec through 8/26/15 has been that
  `logDensityOfCounts` returns log p(x_i|theta), however

- The name `logDensityOfCounts` is more suggestive of log p(t|theta),
  since t is the counts.

- Further, for M-H acceptance ratios it doesn't matter, because as
  p(x_i|t) does not depend on theta,

    log p(x_i|theta_1) - log p(x_i|theta_2)
    = log p(t|theta_1) - log p(t|theta_2).

- Still further, for rejection sampling it doesn't matter either, as
  long as the bound given by `madeSpLogDensityOfCountsBound` is
  consistent.  For discrete distributions, the default of 0 will be
  consistent in both cases, but tighter for log p(t|theta) (thus
  leading to a higher acceptance ratio).  Conversely, while
  `logDensityOfCounts` continues to return log p(x_i|theta), the
  discrete bound can be tightened to log p(x_i|t).

- By exchangeability of the SP in question, p(x_i|t) is equal for all
  permutations of the data sequence x_i.  On the one hand, this is
  what enables computing it from a brief summary, but on the other
  hand, why try to distinguish a single sequence instead of summing
  the probability over all of them that are compatible with the
  statistic t?

There are, however, situations where the precise interpretation of
`logDensityOfCounts` does matter.

- An exact spec gives meaning to the total weight of a particle set
  over a model that contains observations of SPs that use
  `logDensityOfCounts`.

- In particular, the particle weights produced by initializing such a
  model from the prior will be computed by incremental application of
  `logDensity`.  However, if the `likelihood_weight` inference action
  is invoked, the new weights will be computed via
  `logDensityOfCounts`.  It is important for these to agree, in case
  the user wishes to form a joint weighted estimate from both.

- This doesn't actually break the symmetry between p(x_i|theta) and
  p(t|theta), because `logDensity` could in principle be arranged to
  produce the latter.

This fact makes the following decision somewhat arbitrary.

Decision
--------

1) Specify that `logDensityOfCounts` returns p(x_i|theta), not
   p(t|theta).

2) Rename `logDensityOfCounts` to `logDensityOfData` to better connote
   this.

3) Leave room for a method of a different name (to be chosen if
   needed) that computes p(t|theta).

Note: The decision (1) has no effect on `gradientOfLogDensityOfCounts`,
because the p(x_i|t) term is additive in log space and its derivative
with respect to theta is zero.

Rationale (spec)
----------------

- Pro: That's what most implementations already compute.

- Pro: It agrees with the current meaning of `logDensity`.  A
  particular manifestation of this is `logDensity` symmetry between
  the compound and non-conjugate-suff-stat versions of the same
  distribution.

- Pro: It simplifies semantics of total particle weights, and
  acceptance rates of global rejection.

- Con: The Poisson distribution's `logDensityOfCounts` method
  computes p(t|theta).

  - Resolution: This non-conformance is a fixable bug (see [issue
    #333](https://github.com/probcomp/Venturecxx/issues/333)).

- Con: p(x_i|theta) cannot in general be computed from just the
  traditional sufficient statistic t.  The Poisson distribution is an
  example: the mean of the data is sufficient for inferences about
  theta, but does not suffice to compute p(x_i|theta).

  - Resolution a: I conjecture that the number p(x_i|t) that suffices
    to convert between p(x_i|theta) and p(t|theta) can always be
    maintained by incorporate and unincorporate, which case both
    candidate specs are always equally easy to implement.

  - Resolution b: Even if not, we can supply p(t|theta) under a
    different name, and teach relevant algorithms to use it if
    p(x_i|theta) is not available.

- Con: If we provided "lifted" versions of SPs, that would accept an
  application count and return values of t, the natural log density
  for those would be log p(t|theta).  Such bulk versions would thus
  not be quite symmetric with the suff stat collecting non-bulk
  procedures discussed here.

  - Resolution: That's OK.  They represent different distributions.

Rationale (name)
----------------

One of source of confusion was that the name `logDensityOfCounts`
connotes p(t|theta), since t is the counts.  We want the new name to
communicate the specification more clearly.  There is another
distinction also worth capturing, if possible, namely that in the
presence of a nontrivial aux, `logDensityOfData` is about the
already-seen sequence summarized by the aux, whereas `logDensity` is
about the predictive distribution, on a new data point, implicitly
conditional on the data in the aux.

Candidate names that were considered:

- `logDensityOfData`, trying to connote the value sequence itself
  rather than the summary.

  - Accepted as an improvement over `logDensityOfCounts`.

- `logDensityOfObservations`, variant of `logDensityOfData`.

  - The data in the aux is not necessarily observed; could be latent.

- `logDensitySampling`, referring to the sampling distribution on data
  already seen.  For contrast, could also rename `logDensity` to
  `logDensityPredictive`.

  - El Goog suggests that many authors whose names are not Jaynes talk
    about the sampling distribution _of the sufficient statistic_,
    which is exactly the connotation we were trying to avoid.

- `logDensityJoint`, referring to the joint distribution of all the
  seen data.

  - Problem: too likely to be confused with the joint between the data
    and some parameters.

- `logDensityOfApplicationSequence`, referring to the fact that the
  data comes from the applications of the SP, and we only want one
  sequence.

  - Too long and unwieldly.

- `logDensityAtApplications`, `logDensityOfApplications`, and variants,
  recalling the association with `childrenCanAbsorbAtApplications`.

  - Too internal.  The concept of p(x_i|theta) is well-defined
    regardless of Venture; no need to saddle SP implementers with the
    mental baggage of understanding the circumstances in which the
    method will be called, and where its input aux will be accumulated
    from.

