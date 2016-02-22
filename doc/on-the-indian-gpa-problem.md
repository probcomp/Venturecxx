On the Indian GPA Problem
Disclaimer: a bit rambling

The Indian GPA Problem is the following:

 "You are a member of the graduate admissions committee at your
  university, and you have a problem with interpreting the applicants'
  grade point averages.  An applicant that went to an American college
  for undergrad will receive a real-valued GPA on a 0-4 scale; and a
  reasonable proportion are strong enough to get perfect 4s.  The
  grading tradition in India is different: an applicant that went to
  an Indian college for undergrad will receive a real-valued GPA on a
  0-10 scale.  The trouble is that applications do not always have
  disambiguating information about the student's country of origin.
  The applicant pool at your university is 50% American and 50%
  Indian.  You are looking at an application that reports a GPA of
  exactly 4.  What are the chances that the student is a strong
  American vs a weak Indian?"

There are various arguments about reasonable ways to pose and answer
this puzzle probabilistically.  The challenge for probabilistic
programming systems is what to do with the following model of it:

```
[assume american_talent (uniform_continuous 0 5)]
[assume american_gpa (if (>= base_american_gpa 4) 4 american_talent)]
[assume indian_talent (uniform_continuous 0 11)]
[assume indian_gpa (if (>= base_indian_gpa 10) 4 indian_talent)]
[assume is_american (flip)]
[assume gpa (if is_american american_gpa indian_gpa)]
[observe gpa 4]
[infer ...]
[sample is_american]
```

In this formulation, the correct answer is that the probability of
being American is 100%, because `(uniform_continuous 0 11)` has
probability zero of landing on exactly 4.  However, Venture's default
Markov chain will screw this up.  If you manage to get a program of
that kind past the dreaded "Cannot make requests downstream of a
random choice that gets constrained during regen" error message, the
M-H test will compare the density of `constant 4` against counting
measure with the density of `(uniform_continuous 0 11)` against
Lebesgue measure at 4 and erroneously conclude that one is 11 times
(rather than inifity times) bigger than the other.

What follows is an extract of thoughts about this problem from my
archive, circa early 2015.

Let's try the rules again.

- In order to be usable as a likelihood [is this a good way to spell
  "absorbing border"?] for an M-H sampling scheme, it suffices for an
  assessor to retain the same base measure and the same normalizing
  constant under changes to its arguments.  In general we permit that
  to be argument-specific [forward reference: the Indian GPA SP will
  be able to absorb the mixing weight but not the spike location].

- In a higher-order language, a proposal may change the applicable
  assessor [this happens in our treatment of exposed IFs, too].
  In this case, coherence is guaranteed if both the old and new
  assessors have the same base measure and the same Z.
  - Example: the assessors of all the made SPs of a (hypothetical)
    uncollapsed gamma-normal have Lebesgue base measure and Z=1.  (But
    would not if we left off the 1/sqrt(sigma) correction to the
    normal density).
  - A basic version of this can be enforced (finger to nose) by
    - declaring a data type of opaque, generative, first-class objects
      named BaseMeasureAndZ
    - predefining individual ones CountingAnd1 and LebesgueAnd1
    - requiring declare-assessor to supply an argument of type
      BaseMeasureAndZ in addition to the assessor
    - (define (declare-mass sim pmf) (declare-assessor sim pmf CountingAnd1))
    - (define (declare-density sim pdf) (declare-assessor sim pmf LebesgueAnd1))
    - checking measure-and-Z compatibility when trying to absorb a
      change of operator.
    - This check can be moved to scaffold construction time, if the
      scaffold construction can statically predict the space of
      possible operators the proposal may generate (which is the case
      when reproposing, e.g., the maker node of
      make_uncollapsed_beta_bernoulli).
    - Exposed compound procedures (i.e. ones without a declared
      assessor of their own) defer to their tail expressions (which
      may depend on how control flows inside the compound).
    - A constant can be veiwed as a nullary simulator that returns
      that constant.  The constant implicitly has full precision, so
      that simulator is implicitly assessed against counting measure.
  - An elaboration towards allowing adjustments would be to define
    (base-measure-and-Z-correction old new) as a generic operation (in
    the CLOS sense) and permit user-defined classes/methods that know
    how to compute corrections for switching between various
    (sub-)classes of BaseMeasureAndZ.
    - Then again, this may not be necessary, because it may be
      possible to choose global representatives for any such classes
      and build the corrections into the assessors that use class
      members.
    - Then again again, there is, actually, a valid correction between
      counting measure and Lebesgue measure, namely 0.  So the above
      thoughts about representatives only admit useful assessors
      within equivalence classes of the "mutual correction is
      non-zero" relation.
  - For structured data, it seems necessary to define compound
    BaseMeasureAndZ objects for every algebraic data type.  (Though
    maybe for using assessors as M-H likelihoods, we only need product
    types, because we know what branch of the sum the actual value is
    in).
  - In the event of a proposal that can't be coherently assessed
    because of proposing an operator change, the two alternatives are
    to reject the transition, or to include that node in the block
    being proposed (if the incompatibility is detected at scaffold
    construction time) (and if that node is not constrained by an
    observation).

- We also use assessors to evaluate the prior in M-H proposals whose
  proposal distributions are not the prior (e.g., slice, hmc).  Since
  the arguments are fixed, these are automatically compatible along
  all dimensions.
  - I have not thought about block proposals whose principal nodes
    have causal dependencies on each other, in which case the above
    glib hack doesn't work.  The rules for likelihoods may suffice.
    - I have even more not thought about block proposals where one
      principal node may change the operator that applies at another.
  - I also have not thought about block proposals where some principal
    nodes are in the brush (that is, are existentially dependent on
    others).  HMC as implemented in v0.2 may crash (haven't checked).

- Aside: I feel like the way I am thinking about this is still too
  glib about control-flow changes.

- Observations require value compatibility checking when initializing
  [which we do not handle very cleanly in v0.2]

- Rejection sampling admits unnormalized assessors and bounds (because
  it always divides), but requires the same compatibility
  considerations, technically across all possible proposals (in order
  for the bounds to be valid).  It also requries the maximum of the
  upper bounds.
  - We can try to dynamically detect violations by recording the
    BaseMeasureAndZ objects that occur at observations across
    proposals, but we can't purely dynamically guarantee compatibility
    across all control paths (and therefore correctness of rejection
    sampling in the face of possible such violations).
  - There may be a tractable and useful static analysis that
    conservatively approximates the base measure and Z compatibility
    property.  Reliably computing the maximum of all the upper bounds,
    however, in the presence of allowing the upper bound procedures to
    vary (even if their base measures and normalizing constants are
    known to be fixed) strikes me as intractable, so I am forced to
    declare rejection sampling dead in the water in the presence of
    control variability that may change the upper bound procedures
    that obtain at the absorbing border.
    - The version we have now assumes that the bounds procedures that
      obtain in the starting state will obtain throughout.  We could
      adjust it to dynamically detect violations of that invariant and
      signal errors.  It may, however, be somewhat incorrect, in that
      it may return (wrong) rejection samples in situations where the
      invariant would have been violated but the violation was not
      detected.
      - Then again, the above hypothetical static analysis might be
        usable to confirm that the bounds procedures do not, in fact,
        change, and get certificates of exactness for easy cases.
  - In the Indian GPA case, the optimally correct answer involves
    discovering the existence of a control path that matches the
    observation with counting measure, and using that to correct the
    acceptance probabilities of all Lebesgue-measure paths to matching
    the observation to zero.
  - Trying rejection on Indian GPA (all three attempted encodings)
    produces "Can't do rejection sampling when observing resimulation
    of unknown code", which is presumably a complaint about computing
    maxima of upper bounds across multiple execution paths.

- Likelihood weighting also admits unnormalized assessors, because we
  can interpret the weights as themselves unnormalized.  Correct
  treatment calls for retaining the compound base measures for all
  particles and using any dominating ones to correct each other.
  - Thus, a (high-memory) likelihood weighting scheme for Indian GPA
    will be correct in the limit, because it will evetually discover
    the counting-measure control path, and correct the weights of all
    past and future Lebesgue particles to zero.
  - We may also be able to statically verify all-paths base measure
    (and Z) consistency (in sufficiently easy cases), thus
    guaranteeing comparability of our weights.  For likelihood
    weighting, though, this doesn't say much, because even if we can't
    experience infinite weights in the future, our conclusions can
    still be invalidated by finding arbitrarily large ones.

- Once initialized, observations are nodes that must be asorbed at,
  which means they do not admit changes of base measure.  In
  principle, we could consider corrections, which would mean that a
  chain would be able to step from a Lebesgue-measure control path to
  a counting measure control path, but not back.  In the case of
  Indian GPA, that should produce the desired result.

- Indian GPA per se has another potential problem, not related to base
  measures, but a consequence of our constraint incorporation
  algorithm.  One way to encode the American component is
    [assume base_american_gpa (uniform_continuous 0 5)]
    [assume american_gpa (if (>= base_american_gpa 4) 4 base_american_gpa)]
    [assume gpa (if (flip) american_gpa indian_gpa)]
  If the gpa variable is then observed, (perhaps during inference) one
  thing that might happen is that the base_american_gpa variable will
  get constrained to 4.  This is actually wrong in two ways:
  - Setting the variable to 4 invalidates the control path that causes
    it to get constrained
  - Even if it didn't (e.g., if I had written > for >= above),
    constraining that variable to 4 forever is inappropriate, because
    it prevents proposals that could change the control path and in so
    doing remove the constraint
  Because of these effects, Venture v0.2 currently disallows that
  situation entirely, crashing with the cryptic error message "Cannot
  make requests downstream of a node that gets constrained during
  regen".  As an engineering choice, we might consider softening the
  impossibility level of this situation to "probability zero" rather
  than "program error", though that may still be somewhat
  counterintuitive.

- Thought: It may be possible to mitigate the above problem, by
  considering the conditionals of IFs to be independent random
  choices, but treating mismatches as zero-probability events.  Not
  clear now well this works; not clear how it scales to applications
  of variable procedures.
  - Testing this out on Indian GPA triggers "Cannot make random
    choices downstream of a node that gets constrained during regen";
    actually, this makes some sense, because if a constrained choice A
    can influence the proposal probability of a control-flow choice B
    that impacts whether A remains constrained, incorrect
    distributions may result.
  - There may be a clever scheme involving blocking the control flow
    choices with the choices whose constrainedness they affect that
    fixes this.
  - It could also work to just not propagate constraints back that
    far.  It's quite possible that the only thing we would lose would
    be computation.

- It is also possible to code around this in Indian GPA, like this:
    [assume overachiever (flip 0.2)]
    [assume american_gpa
      (if overachiever 4 (uniform_continuous 0 4))]
  Or like this:
    [assume overachiever (>= (uniform_continuous 0 5) 4)]
    [assume american_gpa
      (if overachiever 4 (uniform_continuous 0 4))]
  It's not impossible that some such form may be derivable
  automatically.
  - Doing this by hand (and wrapping the constant in a "random" choice
    that always produces it with probability _mass_ 1) suffices to get
    Venture v0.2 to produce the wrong answer without erroring out.

- Actually, the situation with the exact Indian GPA SP is even more
  comical: if the spike location changes, it is acceptable to form the
  mutual dominating measure of the old and proposed state (which has a
  spike at the old and new place) and assess the density of the output
  with respect to that.  If the output is at neither spike location,
  then the sitation is as good as uniform.  If it is, though, and the
  locations are distinct, then one or the other assessment should, for
  correctness, be zero, ensuring certain or impossible acceptance.
  - General interface covering this: an "assessment ratio" procedure
    that accepts the old arguments, the new arguments, and the value,
    and returns the ratio.
  - If a normal assessor is available:
    (define (assessment-ratio-calculator assessor)
      (lambda (val old-args new-args)
        (/ (apply assessor val new-args) (apply assessor val old-args))))
    which is of course what detach/regen conspire to accomplish.
  - An assessment ratio procedure can also incorporate corrections for
    compatible changes in base measure, and for differences in Z (if
    it can compute them) (note: only the Z ratio is needed, which may
    be more tractable than separately normalizing both assessments).
  - This interface annoys me, because it looks more and more like a
    very special-purpose hook into a particular (class of?) algorithm.
  - On the other hand, (assess val old-args) can be represented as
    the (hand to inspect) object
      (lambda (new-args) (assessment-ratio val old-args new-args))
    Perhaps we can define an adequate interface for ratio-only
    assessors in detach/regen by allowing an "assessor" to return an
    opaque object such as this.  (We would need to define subtraction
    on two such things to extract the args captured by one and feed
    them into the other.)  Then the only obligation becomes to make
    sure the addition of the detach and regen weights cancels the
    correct ones against each other (which can probably be arranged by
    matching addresses).

- Maybe we should solve discrete and continuous versions of the
  Hierarchical Indian GPA problem, where one also infers the locations
  of the cutoffs.  (The variation being in whether the prior on the
  cutoff is discrete or continuous.)
  - This feels like research to me.  Do we have the luxury of
    switching to that mode?

----------------------------------------------------------------------

Another attempt to say it:
- Measures are all well and good, but
  - Algorithms (rejection sampling, importance sampling, resimulation
    M-H) want to work with limits of set-based queries.
  - Those limits are known for many (most?) primitives.
  - The corrections usually cancel.
- The difference between a probability mass function and a (1D)
  probability density function is that the former represents the point
  limit
    pmf(x) = lim_{eps -> 0} Pr(eps-ball-near(x))
  whereas the latter represents the point limit [*]
    pdf(x) = lim_{eps -> 0} Pr(eps-ball-near(x)) / eps
  because without dividing by eps the limit is zero.
- To work with these things in a unified framework, why not include
  the eps as a formal object?
  - We can try to compile away references to eps and datastructures
    containing it later -- it will be some time before that is our
    dominant performance problem.
  - Do we need to distinguish different eps for different coordinates
    of a multidimensional object?
  - What about objects that are lower-dimensional than they appear,
    because the SP emitting them enforces some deterministic
    relationship?

[*] I presume this is actually the Radon-Nikodym (sp) derivative of
the density of interest against Lebesgue measure, subject to all the
usual existence conditions thereof.

----------------------------------------------------------------------

Possible resolution: "There is a strict version that rules Indian GPA
out and admits such and so workarounds, defined by the needs of
rejection sampling; the Venture system implements some
non-conservative relaxations for programmer convenience that cause it
to give wrong answers; there is a way to package the thing as an SP."

----------------------------------------------------------------------

Summary of the Indian GPA problem
- It's a base measure compatibility problem
- Fuzzing the observation in a variety of ways solves it
- Annotating primitive procedures with measures, or their densities
  with base measures, should let a generic algorithm detect the
  problem
- Should in principle be possible to write an SP that does the right
  thing, and can be used in a component of a hierarchical model.

Venture v0.2 disallows the obvious program, either because
- "Cannot constrain a constant value" (this is hackable); or because
- "Cannot make requests downstream of a node that gets constrained
  during regen" (namely base american gpa participating in both the
  condition and the result of the max); or because
- AssertionError "assert node in self.ccs" (this indicates a bug in
  Lite -- no user program should trigger assertion errors in the
  engine).
- None of these are quite the error messages I was looking for.
- Fuzzing the observation in any of a number of ways fixes it.

The measure-theoretic answer is of course "Indian is impossible",
because the limit of anything sensible as epsilon goes to zero is
that.
- There's a choice: we can take the limit as a ball around the
  observation goes to zero, or we can take the limit as a ball around
  the exact preimage of the observation under the model goes to zero.
  - If the model is continuous in the assumed uniform base randomness,
    these two limits will be the same, but I intuit that they need not
    be if the model is discontinuous.
  - The intermediate answers at various epsilon will in general be
    different (though Indian GPA specifically may be linear enough not
    to exhibit this phenomenon).
- To implement this for real we need to either
  - compute pre-images (ha!), or
  - define a general metric on all objects with components that we
    wish to be able to treat continuously, or
  - work with limits after all.
  - The general metric approach may actually be doable, with some
    work; it feels similar to the work we have to do (have mostly
    done?) to make gradients well-defined.

The reason the Indian GPA conclusion is unintuitive is that GPAs are
never reported exactly, but rounded to about 1 decimal place of
precision.  So the Indian student actually has a probability of around
1% of having their GPA reported as 4.0 (rather than 3.9 or 4.1); the
net effect favors the American by about 20 to 1, but certainly admits
the Indian as a possibility.
- Can implement this in Venture with a round function
  - Rejection sampling will work
  - MCMC will in principle work too, after a satisfying a assignment
    is found (though mixing is likely to suck)
  - If round is a beast that can compute useful preimages, more
    efficient algorithms may be possible

This actually suggests a Finitary Finiversalist answer: all base
measures are the counting measure on representable objects.  Then
even "continuous" distributions actually have probability mass
functions, which give the probability of getting that particular
floating point number.
- The true answer for any density is the integral of said density
  between half-way to the next float down and half-way to the next
  float up.
  - This can be approximated by evaluating the density here and
    multiplying by the size of one ulp.
    - One source of error: truncation error in the integral, which
      will be second order except at roll-over points.
    - Another: the size of the area of integration will be funny at
      points where the ulp size changes.
  - Actually, the real true answer depends (slightly) on the rounding
    mode, but I don't want to go there implementationally.
- Sadly, I expect these pmfs not to be preserved exactly by
  transforms; e.g., I expect the actual pmf of the box-muller
  transform applied to a pair of thus-discretized uniforms not to be
  quite equal to the pmf of "sample an ideal Gaussian and then round
  to the nearest floating point number".  This slightly changes the
  "gentleman's agreement".
- If both distributions being compared are "continuous" (and of the
  same dimensionality), the correction for being a float will cancel
  and produce exactly the same answers as the density directly.
  - Unless we take a cleverer integral than the simple one-point
    approximation outlined above; then there may be other artifacts.
- In the general case, the answers will depend on the bit precision;
  but that happens with floats anyway.
- The Indian GPA gets a funny twist: if you write the max to produce
  an exact result, then it will actually never be the same object as
  the float, and the observation will be able to peg it.
  - Unless explicitly type-converted one way or the other.
- Assuming an all-floating model definition, the answer will now favor
  the American by on the order of 2^52 to 1, but still not infinity.
  - This is only about as bad as being 8-9 standard deviations out on
    a Gaussian.
- Actually implementing this story in a sane way calls for an
  abstraction for the correction, which amounts to SP authors tagging
  their SPs' outputs as continuous or discrete.
  - Could do it for illustration by making some custom SPs.
  - No sampler will distinguish 1 in 2^52 from 0 in a direct test.

Aside: Exact rationals become a problem, because uniform sampling from
the unit interval in exact rationals is not actually possible -- the
probability of every possible result is actually zero.

Do we want to claim to detect cases where proceeding naively (without
the continuity correction) will cause mistakes?  One way to do that is
to implement the correction with a symbolic guard and warn if it
doesn't cancel.

All this rounding business amounts to the same thing as positing
uniform noise on the observation.
- Do we want to work out the exact relationship between rounding
  precision and noise size?  I intuitively assume it depends on the
  model, but that may not be so.

Assuming Gaussian noise on the observation is spiritually similar to
the preceding.  It is less well-justified by the details of a small
floating-point computation, but better justified as a model of error
compounding in a long one (where the variance of the Gaussian depends
on the length of the computation!).

One can also fix the Indian GPA problem by assuming a noisy_true style
noise model, where the observation has some fixed probability of being
spurious.
- Setting this probability to be small favors the American.

About encapsulating the thing in an SP: The natural one that comes to
mind cannot absorb changes to the location of the spike, because the
base measures for the density will be incomparable.
- May be possible to justify one that always rejects proposals to move
  the spike away from agreeing with the datum
- I think there may be a zero/zero problem for proposals to move the
  spike into agreement with the datum.
- This is a test for our SP interface: can we spell it out clearly
  enough that a rules lawyer reading the documentation will know how
  to write the Indian GPA SP (or the American GPA component of it)?
- Do we have the obligation to write SPs like "max" so that they
  propagate these funny measures?  Is there a clear rule statement we
  can state that implies that we don't?
