Example programs:

1) Modeling in terms of inference:

  [ASSUME infer-param (mem (lambda (val prior_var)
    [ASSUME theta (normal 0 prior_var)]
    [OBSERVE (normal theta 0.1) val]
    [INFER (mh default one 10)]
    theta))]

  [ASSUME variance_used (gamma 1 1)]
  [OBSERVE (normal @(infer-param 10 variance_used) 0.5) 10)]
  [PREDICT variance_used]

- The infer-param distribution, as used, should look generative;
  should not modify the value of variance_used.
- Inference in the outer model must, of necessity, treat infer-param
  as likelihood-free.

2) Conditional observation and inference:

  [ASSUME is_trick (bernoulli 0.1)]
  [ASSUME weight (if is_trick (uniform_continuous 0 1) 0.5)]

  [ASSUME add_data_and_predict (lambda ()
     [OBSERVE (bernoulli weight) True]
     [INFER (mh default one 10)]
     )]

  [ASSUME find_trick (lambda ()
    (if (not is_trick)
        (begin (add_data_and_predict) (find_trick))))]
  [PREDICT (find_trick)] ; returns no useful value but needs to be run
  [PREDICT weight] ; quantity of interest
  ;; At this point, is_trick is true, and there is some distribution
  ;; on the weight and the number of observations in the trace

- This example is Alexey's misinterpretation of Vikash's example
  from the July 7 notes.
- Inference should be able to read from the trace being inferred
- Observations and inference in non-extended compounds should be able
  to affect the caller's distribution

2') Conditional observation and inference:

  [ASSUME is_trick (bernoulli 0.1)]
  [ASSUME weight (if is_trick (uniform_continuous 0 1) 0.5)]

  [ASSUME add_data_and_predict (lambda (t)
    (let ((_ t' _) (eval '[observe (bernoulli weight) True] t (get-current-environment)))
      ((mh default one 10) t')))]
  [ASSUME find_trick (lambda (t)
    (let ((now_trick? _ _) (eval 'is_trick t (get-current-environment)))
      (if (not now_trick?)
          (let ((t' (add_data_and_predict t)))
            (find_trick t'))
          t)))]
  [INFER find_trick]

  [PREDICT weight] ; quantity of interest

- Here is a version of what Vikash might have actually meant, written
  in the (more) uniform language in Alexey's head.

3) Inference by modeling:

  [ASSUME some stuff]
  [OBSERVE some stuff]
  [INFER (lambda (t)
    [ASSUME some meta-stuff]
    [OBSERVE some meta-stuff]
    [INFER ...]
    t')]

- I think it is reasonable to say that the inner INFER cannot see the
  changes it is making to the enclosing model via its lexical
  environment, only by inspecting the reified trace object t.

4) Model extension upward funarg problem (with nested inference):

  [ASSUME dev (gamma 1 1)]
  [ASSUME f @(lambda (y)
    [ASSUME z (normal y dev)]
    [OBSERVE (normal z dev) 10]
    [INFER (mh default one 1)]
    z)]
  [PREDICT (f 1)]
  [PREDICT @(f 1)]

- What should the distributions on the two predicts be?
  - Is it affected by their order?
- Is f likelihood-free even if spliced?
  - Perhaps not.  Perhaps there is no infer node if f is spliced.
- If f was not declared extending, the above program would (I think)
  be equivalent (up to observability in the lexical environment) to

  [ASSUME dev (gamma 1 1)]
  [ASSUME f (lambda (y)
    [ASSUME z (normal y dev)]
    [OBSERVE (normal z dev) 10]
    [INFER (mh default one 1)]
    z)]
  [ASSUME __z_1__ (normal 1 dev)]
  [OBSERVE (normal __z_1__ dev) 10]
  [INFER (mh default one 1)]
  [PREDICT __z_1__]
  [PREDICT @(f 1)]

4b) Model extension upward funarg problem again

  [ASSUME dev (gamma 1 1)]
  [ASSUME f @(let ((true-dev (normal dev 3)))
    @(lambda (y)
      [ASSUME z (normal y true-dev)]
      [OBSERVE (normal z true-dev) 10]
      [INFER (mh default one 1)]
      z))]
  [PREDICT (f 1)]
  [PREDICT @(f 1)]

- What about this one?
- What if the lambda is not declared extending?

4c) Model extension upward funarg problem again, with more inference

  [ASSUME dev (gamma 1 1)]
  [ASSUME f @(let ((true-dev (normal dev 3)))
    [OBSERVE (normal true-dev 2) 1]
    [INFER (mh default one 10)]
    @(lambda (y)
      [ASSUME z (normal y true-dev)]
      [OBSERVE (normal z true-dev) 10]
      [INFER (mh default one 1)]
      z))]
  [PREDICT (f 1)]
  [PREDICT @(f 1)]

- What about this one?

5) I don't think the downward funarg problem is too bad here

  [ASSUME dev (gamma 1 1)]
  [ASSUME f (lambda (y)
    [ASSUME z (normal y dev)]
    [OBSERVE (normal z dev) 10]
    [INFER (mh default one 1)]
    z)]
  [PREDICT @(let ()
    [ASSUME foo (f 1)]
    [OBSERVE (normal foo 1) 4]
    [INFER (mh default one 5)]
    foo)]

- What is the scope of the INFER inside the call (f 1)?
  - Can it fiddle with dev?  (Presumably not)
- What sorts of things can happen during the inference in the let?
- Is this program equivalent to

  [ASSUME dev (gamma 1 1)]
  [PREDICT @(let ()
    [ASSUME __z_1__ (normal 1 dev)]
    [OBSERVE (normal __z_1__ dev) 10]
    [INFER (mh default one 1)]
    [ASSUME foo __z_1__]
    [OBSERVE (normal foo 1) 4]
    [INFER (mh default one 5)]
    foo)]

It occurs to me that Kernel has a version of this problem: read access
is inherited lexically, but write access is not.  It is, however,
possible to grab a write permission (by calling
'get-current-environment' or such) and give it a (lexically scoped)
name, such that it can then be used.  This solves the problem that a
given place may have multiple write permissions in place
simultaneously.  On the other hand, Kernel does not permit reflection
into the structure of the environment the way Venture does, so there
is no question of enforcing write permission boundaries on such
reflection.
