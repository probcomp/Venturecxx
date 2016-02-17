In a Lisp, there are these things:
- expressions
- environments
- bundles of the two (closures)
- primitive procedures that can compute things

A "fully flexible" Lisp can reflect on expressions and environments,
and reify computed expressions and environments as computations.
Facilities for this:
- get current environment, an empty environment, some procedure's
  environment
  - manipulations of environments as data structures
- quote reifies (fixed) expressions
  - manipulations of expressions as data structures
- eval reflects computed expressions and environments back into
  computations
- macros of various flavors get to reify the expressions of their
  arguments and the environments present at their call sites in
  various ways, and then reflect computed expressions and environments
  in various ways.
- it is feasible (see Kernel) to expose environments with limited
  permission to write (and (potentially different) limited permission
  to read).

In a Venture, there are all those things, and:
- a trace
- some primitives can report their densities, which we like
  - also tracking sufficient statistics, doing AAA, and having
    latents, but these are either orthogonal or implementable

So a "fully flexible" Venture should be able to reflect and reify all
the above, and also reify and reflect traces.
- Infer accepts a function that
  - accepts a trace view as data and munges it returning nothing
- Infer thus reifies into that function, and reflects through
  the mutation available to that function
- Operations on traces as data:
  - Get to a node
  - Read it
  - Write to it
  - Call some PSP, ask for the log density, etc.
  - If you want to be coherent, you can write the M-H test yourself
  - See also "semantics", below
- One idea that makes this less mind-bending to think about is:
  - run the function being inferred in a different trace
    - it can do inference itself, which then doesn't interfere, and
      isn't interfered with
- I said "view on a trace".  This is a way to scope the accessibility
  of stuff.  For instance, an infer command that appears in the body
  of some generative compound might see a view on the trace that said
  body is embedded in to which the arguments of the compound (and the
  nodes visible in the enclosing lexical environment) appear as
  constant nodes.
  - Another profit from the idea of "view on a trace": that view can
    actually be a view on a particle, if some external inference thing
    is running this compound and wants to be able to revert any crazy
    mutation that this compound may be doing.
- What does all this have to do with scope_include?  The view on a
  trace that infer sees would be a datastructure that can do some
  various sorts of indexing and lookup operations: starting at a root
  (like the entry point into the generative compound one is in),
  wandering around along path segments, looking things up by name.
  scope_include can register nodes as having names.  The names
  themselves don't have to be symbols, but could perhaps also be
  objects (gensyms?) which can appear in various lexical scopes and
  get referred to.
- Implementation:
  - a view on a trace is a VentureValue
  - a view on a node is a VentureValue
  - entering an infer instruction starts a new trace, whose initial
    environment has views on various things in the enclosing lexical
    scope
  - a (compound) SP doesn't much care what trace its maker node is in,
    but can make its requests and expand its body, etc, in any trace.
  - maybe mem shouldn't work across traces; this can be arranged by
    making the identity of the trace be part of the key in the lookup.
  - all the gkernels and combinators and things that we have now
    become exposed as procedures in the initial environment of the
    initial trace; but perhaps there is no way to call them without a
    trace (or an object that can only be derived from a trace) to pass
    in, so in effect they can only appear nested in at least one level
    of infer.
- Semantics: If the inference function just executes forward without
  problems, the semantics of the whole thing is mutation in
  distribution on the underlying trace (or trace view).  Issue: how do
  we relate the semantics of the function called by inference,
  including it itself doing inference over things that may or may not
  include invocations of "mutate the reified trace", to the overall
  semantics?
  - One style of answer is to define a semantics for a probabilistic
    program on both its return value and the mutations it accomplishes
    to some external object (in this case, the reified trace).  I am
    not sure what the answer in this style would be.
  - Another answer is to restrict the inference program to effectively
    operate only on a particle, and then commit only at the end.  Then
    the semantics of the inner program are essentially over the
    particle it will attempt to commit (or even just return!), and the
    semantics of the outer program involve mutation in distribution
    given by that distribution over possible mutations.
