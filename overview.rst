Overview
--------

Venture programs consist of a series of instructions which are
executed by the Venture SIVM (Stochastic Inference Virtual
Machine).  These instructions

- Build up a generative model for some phenomenon of interest
  (`assume`),

- Include events on which that model is to be conditioned (`observe`),

- Specify queries against that model (`predict`),

- Invoke inference to explore the space of explanations of the events
  that the model judges as plausible (`infer`), and

- Preform various additional and supporting functions (the others).

The "meaning" of a Venture program is the (joint) distribution on
model variables and predictions that executing the program induces.
The major instructions affect the meaning as follows:

- `assume` and `predict` extend the state space of the
  distribution with additional variables or predictions, respectively.
  The marginal of the extended distribution with respect to the
  previously extant variables and predictions remains unchanged.

- `observe` records an event as having occurred, but *does not alter
  the current distribution*.  Instead, `observe` sets up an **implicit
  conditional** distribution.  The implicit conditional is obtained
  from the distribution given by all `assume` s and `predict` s,
  ignoring `infer` s, by conditioning on all `observe` s.  The implicit
  conditional only affects the meaning of a Venture program through
  the invocation of `infer` instructions.

- `infer` mutates the distribution by executing the inference program
  given to it.  Typical inference programs move the distribution
  nearer (in KL-divergence) to the implicit conditional given by all
  executed `observe` s.  For example, `[infer (mh default one 100)]`
  mutates the distribution by taking 100 steps of a certain standard
  Markov chain, whose stationary distribution is the implicit
  conditional given by the preceding `assume` s, `predict` s, and
  `observe` s.

For a more extensive conceptual introduction to Venture, see the
`draft Venture paper <http://arxiv.org/abs/1404.0099>`_.

