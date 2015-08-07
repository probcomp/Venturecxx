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

It may be possible to use numerical techniques like [Richardson
extrapolation](https://en.wikipedia.org/wiki/Richardson_extrapolation)
(on the number of sample points) to reduce the approximation error,
but I am surprised not to find any literature on that.  You'd think it
would be published and readily accessible if it worked.

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
