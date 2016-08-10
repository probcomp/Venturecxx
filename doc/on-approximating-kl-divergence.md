Approximating K-L Divergence
============================

The Kullback-Leibler divergence of Q from P is defined, in the general
case, as the expectation under P of the log of the Radon-Nikodym
derivative of P with respect to Q.

In the discrete case, that reduces to

  E_{x~P} [ln P(x) - ln Q(x)]

If both P and Q are absolutely continuous with respect to any
on measure mu, the K-L divergence is

  E_{x~P} [ln p(x) - ln q(x)]

where p and q are the density functions.

Assessable Case
---------------

If both P and Q are assessable, and P is samplable or enumerable, we
can just compute the integral directly.  If we estimate the integral
by sampling, we need to admit the approximation error, because getting
to machine precision with an O(n^1/2) convergence rate will take
around 2^100 samples.

One might think that it may be possible to use numerical techniques
like [Richardson
extrapolation](https://en.wikipedia.org/wiki/Richardson_extrapolation)
(on the number of sample points) to reduce the approximation error,
but you can't.  I thought it through; the essential reason is that the
approximation error from Monte Carlo integration is (intentionally!)
unpredictable, so can't be extrapolatd from.  I am surprised not to
find any literature on this; the question is so obvious that even a
description of the negative result would be socially valuable.

Aside: Tail Assessable Distributions
------------------------------------

Define a _tail assessable_ representation of a probability
distribution Q over objects of type `a` as a samplable distribution
Q_s over assessable distributions Q_a over objects a.

```haskell
type TailAssessable a = RVar (RVar a, a -> R)
```

The distribution this represents is the join of Q_s Q_a.  In
probability terminology, Q_s is a distribution over some latent state
that we can only (tractably) simulate from, and Q_a is a conditional
distribution over outputs that we can evaluate for any given value of
the latents.

Assessable distributions are a special case of tail-assessable
distributions with no latent state.  Completely likelihood-free
distributions are a special case of tail-assessable distributions with
no non-latent state (and therefore a trivial and unhelpful assessor).

Tail-assessable distributions compose by treating the output of the
first distribution as part of the latent state of the composition:

```haskell
bind :: TailAssessable a -> (a -> TailAssessable b) -> TailAssessable b
bind m f = do         -- in the RVar monad
  (sampler1, _) <- m
  a <- sampler
  (sampler2, assessor2) <- f a
  return (sampler2, assessor2)
```

The compositionality and the existence of a family of initial
tail-assessable distributions together suffice to ensure that a great
many distributions of interest are, in fact, non-trivially
tail-assessable.  In particular, the predictive distribution of any
training strategy applied to a typical Bayesian model will generally
be tail-assessable, because there is some assessable distribution data
values in the model (for example, the one that forms the likelihood of
the observations).

A tail-assessable distribution with a non-trivial assessor can be
approximately competely assessed by sampling many latents and
averaging the assessments.

```haskell
approximately_assess :: Int -> TailAssessable a -> RVar (a -> R)
approximately_assess ct dist = do
  assessors <- liftM (map snd) $ replicateM ct dist
  return (\x -> average $ map ($ x) assessors)
```

As the input `ct` goes to infinity, this distribution on assessors
converges to a spike at the true assessor of the input `dist`.

Tail Assessable Case
--------------------

Returning to K-L divergence, if P or Q are tail assessable, we can
approximate the K-L between them by forming an approximate complete
assessor with `approximately_assess`, and proceeding to estimate the
K-L integral as in the fully assessable case.  Now there will be two
interacting time-accuracy knobs:

- The number of independent latent samples from which the approximate
  assessments are formed.

- The number of samples at which the approximate assessments are
  evaluated.

I do not know any reliable techniques for efficiently reducing such a
tableau to a confidently assertable answer, but the tableau is better
than nothing.

Aside: Tempting alternate analysis.  One can consider the following
procedure:

```haskell
one_point :: TailAssessable a -> TailAssessable a -> RVar Double
one_point query_d base_d = do
  (_, q_assess) <- query_d
  (b_sample, b_assess) <- base_d
  point <- b_sample
  return (b_assess point - q_assess point)
```

This is a one-point estimate of the KL divergence of `query_d` from
`base_d`, in that both are transformed by `approximately_assess 1` and
tested at one point.  This is tempting becuase it reduces two
dimensions of limits to one, but wrong, because the expected value of
this is not the KL divergence.  Why not?  Because expectation does not
distribute over KL.  Counterexample: consider computing the KL
divergence of a bimodal mixture from itself, treating it as tail
assessable over choice of mode in one instance but assessing it end to
end in the other.

Notes
-----

For discrete or low-dimensional distributions, quadrature would be
much faster than Monte Carlo, and may be drivable to machine precision
(obviating the need for dealing with significant approximation
errors).

All the above depends upon the assessments being normalized.  If the P
and Q densities were scaled by the same normalization constant it
would cancel, but how often does that happen?
