As of 8/26/15, we have a persistent problem with the interpretation of
the logDensityOfCounts method.  Time to geek out.

Context: consider a sequence of applications of some SP.
Structurally, think common parameters theta shared between multiple
calls to a thunk:

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

where p(x_i|t) is (for any given data set) a constant that does not
depend on theta.

The incorporate and unincorporate methods of the appropriate SP object
can be arranged to maintain the appropriate value of t.  The issue
is how to define what the logDensityOfCounts method should return.

The current spec is that logDensityOfCounts returns log p(x_i|theta).
Issues:

- The name logDensityOfCounts is more suggestive of log p(t|theta),
  since t is the counts.

- For M-H acceptance ratios it doesn't matter, because as p(x_i|t)
  does not depend on theta,

    log p(x_i|theta_1) - log p(x_i|theta_2)
    = log p(t|theta_1) - log p(t|theta_2)

- For rejection sampling it doesn't matter either, as long as the
  bound given by madeSpLogDensityOfCountsBound is consistent.  For
  discrete distributions, the default of 0 will be consistent in both
  cases, but tighter for log p(t|theta) (thus leading to a higher
  acceptance ratio).  Conversely, while logDensityOfCounts continues
  to return log p(x_i|theta), the discrete bound can be tightened to
  log p(x_i|t)

- p(x_i|theta) cannot in general be computed from just the sufficient
  statistic t.  Poisson is an example.  Perhaps beta bernoulli (and
  dirichlet-style distributions generally) were historically
  misleading here, because in those cases t suffices to determine the
  data completely up to permutation.

- Relatedly, if we provided "lifted" versions of SPs that accept an
  application count and return values of t, the natural log density
  for those would be log p(t|theta).  Such bulk versions would thus
  not be quite symmetric with the suff stat collecting non-bulk
  procedures discussed here.

- Because the specified thing is not always computable and the
  normalizing constant mostly doesn't matter, there may be some
  logDensityOfCounts methods (poisson, crp?) that already violate this
  spec.

Proposal: redefine logDensityOfCounts to return p(t|theta).  Issues:

- Would need to change the formulas in all the current
  logDensityOfCounts implementations, for which we have few good
  tests.

- Would lose symmetry between the suff stat SP and its
  stat-non-collecting version.

- p(t|theta) is not the probability of the actual observed data,
  (somewhat) impeding the ability to, for example, use the acceptance
  rate of a rejection sampler as a way to estimate the probability of
  the data under the model.

1/11/16: Additional proposal: when available, provide access to both.
- One way to do this would be to augment the above proposal with an
  optional method named along the lines of
  "logDensityOfCountedSequence", or
  "logDensityOfCountedSequenceCorrection", the latter returning the
  difference.
- It may also be possible to maintain the constant p(x_i|t) alongside
  the sufficient statistic t.

Note: This decision has no effect on gradientOfLogDensityOfCounts,
because the p(x_i|t) term is additive in log space and its derivative
with respect to theta is zero.
