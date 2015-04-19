Overview
--------

VentureScript is a probabilistic programming language for the Venture
platform that aims to be sufficiently simple, clear, concise, and
expressive for general-purpose use. VentureScript programs specify
sequences of modeling assumptions, observations, queries, and
inference instructions. Data, queries, and other constraints can be
added and removed incrementally, and these operations can be freely
interleaved with inference.
VentureScript is designed to make common modeling and inference tasks
easy, whether or not they are typically formulated in a
probabilistically coherent way.

Intuition
=========

VentureScript programs have multiple meanings:

- The `declarative semantics` is the full Bayesian posterior
  on executions of the program's modeling instructions, conditioned on
  all observations being satisfied. Many distinct programs have the
  same declarative semantics, i.e.  encode the same idealized Bayesian
  inference problem. This distribution will often be intractable to sample from.

- The `procedural semantics` is the distribution over model
  execution histories the full program, including inference
  instructions, actually induces. This distribution is sampled from by
  running the program.

- Various `intermediate semantics`, each defining equivalences
  between programs that ignore some execution details but retain
  others. Some correspond to standard non-Bayesian theories of
  inference, e.g. global joint density optimization semantics.

For a more extensive conceptual introduction to Venture, see the
`draft Venture paper <http://arxiv.org/abs/1404.0099>`_.

