Towards a Grand Unified Theory of Latents
Anthony Lu and Alexey Radul, 3/24/16

Consider an SP that represents a distribution on y with a latent z,
given arguments x.

```
p(y,z|x) = p(z|x) p(y|x,z)
```

What kinds of M-H type moves can it cooperate with, and what does it
need to be able to compute in order to cooperate with them?

The probability features that turn out to be interesting:
1) Basing the proposal to z on the value(s) of y
2) Being able to combine with an arbitrary proposal to x to form a
   block proposal to x and z
3) Block-proposing z and y, and being able to cooperate with feedback
   about how good the ys are (i.e., being rejected)

Additional computational phenomena:
4) Being able to deal with a plate of y
5) Suppressing Venture's traversal of the y nodes, by purporting
   to account for their values
6) Being able to deal with different kinds of y that behave
   differently on the above criteria
7) Being able to efficiently batch propose the whole plate of y

Generally, it seems reasonable to require all such things to be
makers:

```
assume foo = make_foo(x)  // z is latent in the object foo
predict y = foo()
```

This way, z and y have separate trace nodes, so can be referred to
unambiguously; and no expressive power is lost.[^lsrs]

Under this assumption,

- (1) is enabled by `make_foo` creating an aux, `foo` maintaining it,
  and the proposal to z reading it.  It requires being able to
  evaluate the M-H ratio, namely

      p(z',y|x) q(z|x,z',y)
      ---------------------
      p(z,y|x) q(z'|x,z,y)

- (2) requires being able to evaluate the relevant term in the
  compound M-H ratio, namely

      p(z',y|x') q(z|x',z')
      ---------------------
      p(z,y|x) q(z'|x,z)

- (2) together with (1) requires being able to evaluate the relevant
  term in the (now different) M-H ratio, namely

      p(z',y|x') q(z|x',z',y)
      -----------------------
      p(z,y|x) q(z'|x,z,y)

  This may be more complicated than (2) without (1), because q may now
  depend on y; and more complicated than (1) without (2), because now
  there's an x' to worry about.

- Ergo, it is appropriate to permit SPs that have (1) without (2)

- (3) requires being able to evaluate the relevant term in the (yet
  different) M-H ratio, namely

      p(z'|x) q(z|x,z')
      -----------------
      p(z|x) q(z'|x,z)

  (y does not appear in this term because it is accounted for in its
  own term; although in the case of a plate of y, there may be some ys
  being block-proposed and other ys that are fixed.)

  In particular, this comes for free if q has stationary distribution
  p(z|x,y_fixed), which includes any valid standalone transition
  kernel. So it seems harmless to require (3) in general, even for
  AEKernels (aside from the implementation burden of reverting the
  state in case of rejection).

- (4) is irrelevant without (1), and is enabled by the same mechanism
  -- simply more than one application of `foo` (provided applying
  `foo` changes the aux commutatively and invertably).  If (4) is
  not desired, `foo` can just act memoized.

- (5) implies the computational burden of (1)

- (6) can be enabled if the maker returns multiple values, and any
  relevant methods that ask about the ability to do (1-5) can give
  different answers for different made SPs (that still share the aux,
  however).  For example, by accepting their index in the tuple of
  made SPs.

- (7) can be enabled by returning SPs with a batch interface (e.g.,
  make_beta_binomial).

- Absent (5), the made SP itself can decide, via `canAbsorb`, whether
  p(y|x,z) can be computed, or whether proposals to z have to block
  the relevant y in with them.

- `foo` can accept arguments harmlessly.

- This story is orthogonal to delta kernels.  The kernel on z as
  described is a delta kernel, but Venture's extant delta kernel
  machinery will handle this cleanly.[^joint-delta-kernels]

Examples:

- Resimulation from the prior is (2-3).

- Current uncollapsed conjugate models are (1-5).  In particular,
  since their proposals q(z|x,y) are from the local posterior, the M-H
  ratio they report needs to include the term p(y|x') / p(y|x).

  - Absent (2), this cancels

  - With (2), they are currently wrong; Issue #455.

  - (3) is handled by detach unincorporating those applications from
    the aux, so that q does not depend on their former values.

- make_beta_binomial would be (1-5) and (7).

- make_beta_geom_bernoulli, with interface

      ```
      assume_values (coin, geom) = make_beta_geom_bernoulli(alpha, beta)
      predict coin() -> Boolean
      predict geom() -> Geometrically distributed integer
      ```

  is an example of (1-6)

- make_translucent_uc_beta_bernoulli, with interface

      ```
      assume (p, coin) = make_translucent_uc_beta_bernoulli(alpha, beta)
      predict coin() -> Boolean
      sample p // The probability that coin comes up heads
      ```

  is another example of (1-6), where the two made results are
  different (coin is AAA, but p has to be resampled and blocked)

- Current AEKernels are meant to be (1) without (2) or (3).

- This implies a new kind of object, namely proposal kernels that
  combine (1) and (3) but not (2).  Perhaps these are only useful
  in combination with (6)?

Action proposals:

- Fix #455

- Extend the interface of LKernels to have query methods for (2) and
  (3).  Should (2) be named `canComputeMarginalLikelihoodRatio`, since
  that's what's called for in the uncollapsed conjugate case?
  Alternate: `canAbsorb[changes to x into the m-h ratio]`.

  - `childrenCanAAA` is the query method for (5)

  - (1) doesn't need a query method because we can just always give
    the SP its aux, and not reading it makes it easier to meet all the
    other interfaces

  - (4) is automatic

- Rewrite AEKernels in Venture to be funny kinds of LKernels, that
  claim (1) but deny both (2) and (3).

  - Implication: they refer to random choices that participate in the
    scope and block system

  - Possible hack: Put them into a special scope for themselves

  - Possible hack: And don't put them into any other scopes

- Implement scaffold sanity checking to obey non-blockability
  constraints (i.e., absence of (2) or (3))

- Implement multiple value returns (6)

  - Possible technique: retain one node for the result of the maker,
    but broaden the concept of a made SP's maker node to include an
    index into the datastructure at that node, and adjust all the
    maker-node-indexed tabled accordingly

  - This calls for broadening the interface for tag methods that refer
    to made SPs to accept an index to identify which made SP is under
    discussion

Questions:

- How does `canAbsorb` fit into this?

- Is this missing the story about backward kernels?

- How to pass arguments to LKernels / AEKernels?

- Generally, how to spell "Please select these random choices, now
  attach these LKernels to them (which will need to be compatibility
  checked) and run that proposal."?

- What are the right generalizations to cooperating with other kinds
  of proposals (slice, HMC, enumeration, variational)?  Do we just
  want to say that LKernels are M-H only, for instance on the grounds
  that their raison d'etre is to take advantage of cancellations in
  acceptance ratios?

  - @luac suggests as possibly relevant "Pseudo-Marginal Slice
    Sampling", Iain Murray and Matthew Graham,
    http://arxiv.org/pdf/1510.02958.pdf

[^lsrs]: Does this pattern subsume latent simulation requests?  Can a
latent simulation request be mechaniced as an exposed simulation
request for a foreign SP that has a latent like this?  I would be much
happier about LSRs if they turned out to just be a shortcut for this
pattern.

[^joint-delta-kernels]: Independently of all this, delta kernels
interact somewhat strangely with block proposals already.  Consider: A
single-site delta kernel q on y given x (never mind latents) must
compute the M-H term

```
p(y'|x) q(y|y',x)
----------------- .
p(y|x) q(y'|y,x)
```

The quantities needed for this, namely x, y, and y', are available
during regen, and the current LKernel interface permits a method
to compute it (`forwardWeight`).

Now consider a block proposal to x and y using this q to propose y.
The correct term to compute at this node is

```
p(y'|x') q(y|y',x)
------------------ .
p(y|x) q(y'|y,x')
```

Those four quantities can be brought into the same place during regen
by querying the omegadb for the old value of x, but the current
LKernel interface does not permit them to be passed in.  Instead,
regen will, in effect, pass x' for x.

This problem goes away for simulation kernels.  Why?  If q doesn't
depend on y, the needed term becomes

```
p(y'|x') q(y|x)
--------------- ,
p(y|x) q(y'|x')
```

and now the unprimed part can be computed during detach, and the
primed part during regen, calling the same method (`weight`) with two
different sets of arguments (unless the kernel needs to use
cancellations across the primed and unprimed parts, which case is
resolvable by requiring the kernel not to claim to be a simulation
kernel).

In the case of (1) together with (3), the above discussion generalizes
to delta kernels that see the old value of the aux, as it was before
detach removed those applications.

Update: Turns out Lite has a clause in `scaffold.py` that detects
whether the parent node of a putative LKernel is also in the drg, and
ignores the LKernel in that case (falling back to prior resimulation).
It also turns out that delta kernels are just off in Lite completely,
because no transition operator sets useDeltaKernels to True.

P.S. @fsaad suggests "On the flexibility of Metropolis-Hastings
acceptance probabilities in auxiliary variable proposal generation",
Geir Storvik. http://folk.uio.no/geirs/publ/wmcmc_storvik.pdf as
possibly relevant.
