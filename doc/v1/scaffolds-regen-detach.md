Architecture of scaffolds, regen, and detach in v1 as of Nov 3 2014.

Scaffold construction and stochastic regeneration along scaffolds is
provided as a library feature of Venture v1 to aid users in
constructing Bayesianly sound transition operators that deal correctly
with
- likelihood-free stochastic procedures and
- existential dependence among variables,
- in the presence of (exchangeable) coupling
The two former phenomena in particular are common in Turing-complete
models (existential dependence arises from the ubiquitous "if"
statement) while being rare or impossible in other formalisms.

Scaffolds
=========

A "scaffold" is a policy determining a set of nodes to visit when
constructing a candidate trace modification, an order in which to
visit them, and the shape of the actions to take at each node.

- This policy is not just a list, because the visitation may require
  evaluating new code (if new variables come into existence during the
  proposal).

- Visitation order is constrained to be consistent with the partial
  order implied by data dependence in the model.  One great advantage
  of exchangeability is that exchangeable coupling is not dependence
  in this sense, because the coupled variables can be reordered past
  each other.

- Consistency impels us to construct scaffolds in advance of any given
  proposal, conservatively computing the possibility of variables
  coming into or out of existence due to the proposal.  More
  "context-sensitive" scaffolds that reuse variables that the proposal
  could have but did not make non-existent are an exciting topic for
  future research.

- Visitation extent is constrained to include the dynamic Markov
  blanket of the proposal, including the reverse proposal.

In order to be able to construct non-global scaffolds, the system
needs to have access some form of dependency information.  In Venture,
this is conveyed by metadata attached to the simulators in the
underlying models.  We adopt the
simulate/assess/incorporate/unincorporate model of model programming
described in assessable-observable-exchangeable.md.

Regeneration
============

Regeneration is an algorithm for computing a proposed new trace and
the importance weight of proposing it against the (local) posterior.
Regeneration is parameterized by the scaffold at which to regenerate,
the proposal distribution for any new values, and any additional
computation the user may wish to perform over the nodes traversed when
forming the proposal.

The posterior factors into (conditional) terms corresponding to the
applications of stochastic procedures.  Typically, the posterior
factor of any given application is counted when traversing that
application, but in some circumstances it may be profitable to count
it when traversing a related application (see TODO "Abosrbing at
Applications").

The actions that a proposal can take at a node are:

- Propose a new value for this variable (this is required of variables
  that the proposal brings into existence).

  - To compute M-H acceptance ratios, it is necessary to know the
    importance weight of proposing that particular value vs the prior
    at this node.  In the common case of proposing by resimulating
    from said prior, that weight is exactly 1; such proposals can be
    applied even to applications of likelihood-free stochastic
    procedures.

- Absorb changes by leaving this variable's value the same as it was
  before.  If any of the arguments to the procedure being applied
  (including any coupled state the procedure may read) changed due to
  the proposal, the posterior factor associated with the application
  needs to be counted.

  - Consequently, this action is only possible at applications of
    assessable operators.

- Ignore the node because the proposal is changing neither the node's
  value nor any values it depends upon.  In this case, the node's
  posterior factor cancels out between the old trace and the new one
  and need not be computed.  (TODO Is that actually the right
  justification?).

  - Note that this action is only possible at applications of
    "controllable" simulators: either ones annotated pure, or ones
    annotated with incorporators, or ones for which the RNG state can
    be effectively captured.  (The latter only works for pure
    resimulation MH, where the value+state-change that I am trying to
    preserve is guaranteed to have come from the procedure itself
    (rather than some funny proposal kernel).)

- Additionally, nodes that are existentially dependent on values a
  proposal is changing ("brush") need to be visited for symmetry with
  the reverse proposal (see next).

For any given scaffold, i.e. schedule of nodes that are to be
proposed, absorbed, brush, or ignored, before a proposal can proceed,
the states of coupled procedures have to be properly prepared.  In
other words, the system must "detach", namely construct a trace where
proposal, absorbing, and brush applications' effects on their coupled
state are not present.  With PET traces this is to be done by
traversing them and unincorporating; with RandomDB traces this is to
be done by rerunning the whole program and only re-incorporating the
ignored nodes.

- At the same time, can compute the importance weight of proposing the
  old trace by regeneration against this scaffold.

- TODO: There is some sophisticated reason why PET detach has to
  traverse nodes in exactly the reverse order as PET regenerate,
  possibly having to do with applications being coupled through data
  dependence as well as internal state.

- If the scaffold calls for any nodes to be ignored that
  a) occur chronologically after the nodes in the proposal, and
  b) are coupled therewith,
  the coupling has to be exchangeable in order for it to be possible
  to perform this construction correctly.

TODO: In the current RandomDB implementation, the brush is
bulk-unincorporated, but not assessed by detach (I had convinced
myself that that was ok once, but most of my examples have no brush).

Characteristics
===============

In light of the above, scaffolds can be characterized on two
dimesions:

- What is resimulated vs absorbed

- What is unincorporated before the proposal vs left in place

These dimensions are not independent, because everything resimulated
(and absorbed nontrivially) has to be unincorporated.

Examples:

- Completely rerunning the program corresponds to resimulating
  everything, even things that could have been absorbed.

- The first RandomDB in v1 viewed as a scaffold, which is now named
  the minimal/maximal scaffold, corresponds to resimulating only the
  target node (and all likelihood-free SPs in the program), but
  including all nodes in the absorbing border and thus (effectively)
  unincorporating all of them.

- The scaffolds that v0.2 constructs on PETs correspond to minimizing
  that which is resimulated and also that which is unincorporated,
  justifying for them the name minimal/minimal.  There is an attempt
  to reproduce the same effect over RandomDB in the current v1
  prototype.

The transition operator difference between resimulation minimality and
maximality is obvious: in the latter case, moves touch all
non-constrained nodes.  Less obvious is that incorporation
minimality/maximality has an effect on the transition operator as
well.  While the set of values changed by any given move is not
affected, the proposal distribution that constitutes "resimulation"
does depend on the choice of what is or is not incorporated when the
proposal is made.

Consider the case of two independent flips of the collapsed coin (this
is the program in the overincorporation.scm test file).
Resimulation-minimal M-H proposes to one flip, leaving the other be.
If the scaffold is also reexecution-minimal, said other flip is (in
effect, regardless of how this effect is implemented) never
unincorporated, so the proposal is conditioned on its current value
through the coupling, and accepted.

If, however, the other coin is (spuriously) added to the scaffold (as
an absorbing node), then the proposal depends on the order in which
stochastic regeneration traverses the program.  In the case where it
traverses the proposal coin first, it will repropose unconditional on
the other, and, due to the coupling, discover a non-trivial weight
when traversing the remaining coin.  If, however, it traverses them in
the opposite order, it will reproduce the minimal-reexecution
behavior.  Presumably both transition operators are sound, but one
presumably converges faster than the other.
