Baseline
========

The underlying Venture interpreter imposes no restrictions on the
behavior of (stochastic) procedures.  In particular, they may have
arbitrary effects, both on internal and external states.  The analogy
is that they run in the IO monad.  Correspondingly, the interpreter
promises no ability to do anything with these procedures except
simulating them forward once.  Including no constraining of their
outputs by observation.

Replay
======

To be able to replay a probabilisitic program safely and consistently
(e.g., for drawing multiple IID samples), all the procedures have to
be more polite.  Refraining from I/O actions and from mutating state
external to the trace to be replayed seems sufficient.
- TODO Precisely characterize the politeness required for (correct)
  replay
  - The whole traced program fragment has to have type Random a
    - Otherwise, any other actions it takes may be repeated,
      interleaved if run in parallel, etc.
  - Conjecture: procedure calls have a type no worse than
      StateT b Random a
    where b is some mutable state captured in the procedure's closure
    and a is the return type, and a does not alias b.
  - That seems sufficient, but may not be necessary, because a
    simulator might mutate state that is inside the trace but is
    visible to other closures as well, and/or may return aliases to
    (some of) the state it mutates.  So at least the state b is the
    global state of the whole program.

RandomDB
========

The policy I would like to implement for RandomDB is "I will tolerate
the same simulators that replaying tolerates, but if you want to be
able to assess them (without breaking guarantees), you have to
characterize their behavior completely, in a form I understand."  This
implies, in particular, that RandomDB is free to skip simulation of an
assessable procedure whose output is known.

In the interest of engineering, I will not attempt to provide the
broadest possible interface to "forms RandomDB understands" for
characterizing simulators.  Rather, the goal is to cover the common
modeling idioms.  As far as I can tell, there are two idioms that are
worth covering:
- Pure simulators return actions of type Random a.  For these, it
  suffices to have an assessor that returns pure functions of type
    a -> Assessment
- Coupled simulators are created with a hidden local state and may
  mutate it; they could have been written in a style that amounts to
  returning actions of type
    StateT b Random a
  For these, it suffices to have an assessor of type
    a -> State b Assessment
  (where I will insist on it actually being pure of that type so the
  RandomDB can choose whether to apply the state change) and the
  ability read and write the state b.
  - Note: RandomDB does not need to impose exchangeability of
    coupling, because it does not reorder computations.
  - Note: This interface imposes an additional restriction on
    simulators that is not apparent from the type signature, namely
    that the state change must be completely determined by (and
    deterministically computable from) the output.  The standard use
    case of implementing collapsed exchangeable models obeys this
    restriction.
- My intuition tells me that it should be possible to cover mutually
  coupled sets of simulators, but I defer that for now.

Additionally, I allow RandomDB to impose the requirement that the
arguments passed to assessables do not alias any state mutated by
anything else (so that storing references to them is effective).
Explicit copying in user code suffices to ensure this.

Design: RandomDB will accept the above two types of metadata under two
different tags, so it knows which is meant.
- The pure case goes under "assessor-tag" and constitutes a procedure
  of type a -> x1 -> ... -> xn -> Assessment for a simulator of type
  x1 -> ... -> xn -> Random a
- The stateful case goes under "coupled-assessor-tag" and constitutes
  a coupled-assessor record.  This record has three fields:
  - get, which is a nullary procedure that reads the state
  - set, which is a unary procedure that writes the state
  - assess, which is a (pure) procedure of type
      a -> b -> x1 -> ... -> xn -> (Assessment, b)
    for a simulator of type
      x1 -> ... -> xn -> Random a
    that contains an internal state of type b whose changes are
    deterministically determined by the inputs and the chosen output a.

Note: the metadata tagging approach permits me to broaden the
interface later by adding more forms under additional tags.

Conjecture: The following interface actually meets the needs of
RandomDB, and imposes fewer style rules on the user:
- a simulate+assess procedure of type
    x1 -> ... -> xn -> StateT b Random (a, Assessment)
  that returns a sample together with an assessment of that sample,
  and performs any desired mutation (the assessment will need to be
  saved because there will be no way to recompute it)
- a mutating-assess procedure of type
    a -> x1 -> ... -> xn -> State b Assessment
  the computes the assessment for a and performs the mutation
  that corresponds to the underlying simulator having produced the
  given a.
Plan: See whether the code for that interface emerges naturally, and
maybe add it under a third tag.

PETs
====

Since PETs need to be able to redo computations incrementally to
accomplish their magic, they will need to impose stricter limits on
the model computations to which their magic is applicable.  I have not
worked the design out clearly yet, but I expect to ban
non-exchangeable mutation, and to require exposing the Abelian group
structure of any exchangeable mutation.  I expect both of these to
apply even to non-assessable simulators, though there may be a set of
primitives from which I may be able to deduce the Abelian group
structure of mutation performed by unannotated compounds.

Observation
===========

For safety, I retain the rule that only assessable operators are
allowed to be observed.  In particular, the strict interpretation of
this implies that it is not permissible to observe un-annotated
compound procedures.

The inability to observe annotated compounds is frustrating.  I took
what was in retrospect a detour, trying to come up with a scheme
whereby some subset of them can be observed.  The result can be
invoked with (infer rdb-propagate-constraints!), but to grok the cases
it handles you currently have no recourse but to read the source.  One
particularity: if the unannotated compounds you are observing are all
constant (recursively), the right thing will happen.  Warning: misuse
may lead to incorrect answers (see TODOs/CONSDIERs in source,
rdb-constraint-propagation.scm).

