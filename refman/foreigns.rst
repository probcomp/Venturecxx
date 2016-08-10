Venture Foreign SPs
-------------------

- What, When, How, Testing support

TODO: Model SPs vs inference SPs vs callbacks; the latter two should
be very easy.

What is a Venture stochastic procedure?
=======================================

Conceptually, a Venture stochastic procedure (SP) represents a
conditional probability distribution, P(output | inputs).

The bare minimum that Venture requires from its SPs is the ability to
sample:

    output ~ P(output | inputs)

TODO: Note that for model SPs, simulate should be a pure function
except for the randomness.  Forward reference to incorporate and
unincorporate for exchangeable mutation.  Also permit a beast like
print whose effects may be repeated.

However, a wide variety of other information about a model SP may be
useful for various purposes:

- Computing the (log) density of the output [#]_ permits

  - Letting the SP define the absorbing border of an M-H proposal

  - Letting the SP be a principal node of an M-H proposal with
    proposal distribution other than the prior

- Computing an upper bound on the (log) density of the output permits
  conditioning on the output when rejection sampling

- Computing the partial derivatives of the log density of the output
  permits conditioning on the output in gradient-based methods (HMC,
  gradient ascent) and letting the SP be a principal node in such
  methods.

- Computing the partial derivatives of the simulation result [#]_
  permits using this SP internally in gradient-based methods (HMC,
  gradient ascent).

- Enumerating the set of possible outputs permits the SP to be a
  principal node in enumerative methods

- One might imagine analogous information being useful for methods
  based on quadrature of continuous variables, but Venture currently
  has no such methods and no means to accept such information.

The Venture SP interface permits one to express all of the above
information and expose it for Venture to take advantage of.

In addition, one might wish to manipulate the sequence of different
outputs that occur from multiple calls to an SP, for instance to

- capture statistics about the whole sequence, especially if they
  are sufficient

- permit the sequence not to be i.i.d (but it must remain
  exchangeable)

- take advantage of conjugacy between the prior on (some part of?)
  the di Finetti measure and its likelihood, either to

  - make Gibbs proposals to an explicit representation thereof, or

  - collapse it out entirely

The Venture SP interface has hooks for this.  See [TODO The section on
exchangeable coupling]

Finally, Venture SPs may need to call back in to Venture.  That is
handled by the request mechanism [TODO link].

Technially, the Venture SP interface also has hooks for attaching
custom proposal distributions and even entire custom inference
programs to individual SPs, but we don't like to talk about that.

.. rubric:: Footnotes

.. [#] Density can be with respect to any base measure (usually
   Lebesgue or counting measure, giving pdf or pmf), as long as the
   base measure is constant across all values of the inputs.  Density
   can also be unnormalized, again as long as the normalization factor
   is constant across all values of the inputs.

.. [#] Yes, this is an unusual thing to do with actually stochastic
   procedures.  See [TODO discussion of gradientOfSimulate].

When should I write a foreign SP for Venture?
=============================================

Writing foreign Venture SPs can accomplish several goals:

- Link with existing foreign modeling or inference code

- Take advantage of sufficient statistics and/or conjugacy (there is
  currently no way to do that with pure-Venture procedures)

- Speed up a computation whose interior is not interesting to trace in
  Venture

- Introduce an operation that should obviously be in the primitive set
  but is missing (recently, atan2).

How do I write a foreign SP for Venture?
========================================

Well, that depends on which SP interface features you want to take
advantage of.

TODO: They are all bound the same way, though: ripl.bind_foreign_sp(name, sp)
or ripl.bind_foreign_inference_sp(name, sp); which you would typically
do in a :ref:`Plugin <plugins-section>`.

Just functions
^^^^^^^^^^^^^^

The easiest kind of foreign SP to add to Venture is just a function
(deterministic or stochastic) that you don't know (or don't care
about) any special properties of.
