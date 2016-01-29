On non-Probability Measures
===========================

Reflecting on experience and Ken Shan's work on Hakaru brings me to
the thought that measures which are not probability measures are
nonetheless very useful objects (at minimum as intermediates before an
eventual normalization).

Such a thing can be represented computationally by a weighted sampler
(what I called an `Importanter`
[elsewhere](http://alexey.radul.name/ideas/2015/how-to-compute-with-a-probability-distribution/#importance-weighting)):

```haskell
type Weight = Double
type Importanter a = Sampler (a, Weight)
```

The (unnormalized) measure of a given importanter, at a set S, can be
defined as the expected weight that occurs in S.  Formally, for `xs`
an `Importanter a` and S a set, the measure `mu_xs` is given by

  mu_xs(S) = lim_{N->inf} 1/N sum [w * I_S(x) | (x,w) <- replicate xs N]

where I_S is the indicator function for S.

The measure `mu_xs` is always a measure.  It will be a probability
measure exactly when the size of the whole space (i.e., the expected
weight) is 1.  It will be a proper measure if the expected weight is
finite and positive, and an improper measure if the expected weight is
infinite.

An unweighted sampler can always be interpreted as a trivially
weighted sampler with all weights equal to 1.  In this case, the
induced measure is provably a probability measure, and this is a good
reason to like unweighted samplers when they can be had.  For general
importanters, however, the expected weight will not necessarily be 1,
and normalizing it to one may require large (formally infinite)
computation.

Mental Consequences
-------------------

- The notion of "exact samples" can be extended to proper
  non-probability measures: We say an importanter is "exact" if all
  the weights are equal to each other.  In this case, each such weight
  is equal to the total size of the measure.

- The semantics for forward simulation of a model program can be
  changed to being an importanter for a potentially non-probability
  measure.  In the classic case of weight being introduced only by
  top-level observations, the size of the resulting measure is exactly
  the model evidence.

- This view suggests that Venture should try to preserve the total
  weight of its particles as an estimate of the size of the measure it
  is dealing with.

Implementation
--------------

- Teach resample to preserve the total weight of the particles, by
  setting each post-resample weight to

      logsumexp(old weights) - log(new # particles)

  - The invariant is that the `logmeanexp` of the weights estimates
    the model evidence

  - Make this hold true for diversify and collapse, too

- Add to the inference language the operation that levels out the
  weights (like resample) but without performing a resampling step.
  This operation is appropriate to do automatically after inference
  has moved the particles to the posterior, but of course we never
  know whether that happened (except for global rejection).  However,
  a user can manually ask that such be done after `mh(default one 100000)`.

Benefits
--------

- This view actually causes nested particle sets to make sense: the
  invariant can be that the average weight in a bag of particles is
  the weight of that bag in the bag it is nested in (if any).  The
  model evidence is the weight of the outermost bag.

  - Implementing nested particle sets sensibly should consist of a
    recursive structure R where any given level contains an inference
    program interpreter and either a single trace or a particle set
    whose members are R.  Doing this can break open several
    long-standing issues at once:

    - Sane particle-specific inference programs (including parallel
      execution)

    - Distributed computing can be injected at one particle set level
      without preventing a user from having multiple per-machine
      particles at a lower level (though, nesting may not be needed
      for this)

    - Specific benefit from having two nesting levels: be able to
      study the behavior of a particle method by running multiple
      indepedent instances of it

- We can permit SP simulation to be weighted rather than unweighted
  sampling by letting the `simulate` (or `apply`) method of an SP to
  emit the weight in addition to the sample.  Any such weight produced
  during forward simulation gets added to the weight of the particle;
  any such weight produced during an M-H step gets accounted for in
  the acceptance ratio.

  - In the presence of such SPs, the `logmeanexp` particle weight
    becomes the model evidence from the initialization distribution
    rather than the prior.

- The above has the effect of permitting SPs to represent
  non-probability measures.  That should be fine.  In the presence of
  such SPs, the "target distribution" now favors control paths
  invoking SPs with size greater than 1, and favors avoiding control
  paths invoking SPs with size less than 1.

- One particular SP that becomes possible is the thing Hakaru calls
  `factor`: Accepts a weight and represents a measure of that size on
  the singleton set.  Operationally, always returns the same thing,
  and emits its argument as its weight.

  - There is a symmetry between `observe (foo x y) 3` and
    `factor(foo_density(3, x, y))`.

- To permit this, the model language will syntax for sequencing, to
  define compounds that contain calls to `factor` or similar but throw
  away their return value.

- We may want an explicit `normalize` operation in the model language
  whose semantics would be that the measure on its output is the
  normalized version of the measure on its input.  Not clear offhand
  whether there is a generic way to implement this, or whether it in
  fact requires inference programming.

  - N.B.: Trying to normalize an improper measure necessarily fails.

Why now?
--------

This all came up because Stan models can have weight without being
explicitly constrained, e.g. by the user writing an increment log
prob statement that doesn't exactly line up with the constrainable
outputs.  What semantics do we want for that?  Are we trying to make
the made SP represent the normalized conditional distribution, or
can it represent the non-probability measure directly?

- In the current system, forward sampling will not emit the extra
  weight in any case, nor can it effectively do that, because
  Venture is not given access to the breakdown of Stan's posterior
  term into the part that corresponds to the sampler in the
  generated quantity block vs the part that does not.

- However, that extra weight will influence inferences.

- In fact, this is true of any SP whose log density does not agree
  with its sampler.
