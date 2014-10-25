- Compound procedures capture the trace they are created in.  When
  making an MH proposal, that trace is the proposal trace.  If the
  proposal is accepted, the proposal trace commits; but any closures
  are still carrying the proposal trace, which now is not the (only)
  trace that traces the lambda expression that created them.  I am
  surprised this phenomenon has not caused any trouble yet.

  - Could it be harmless because all closures so far are consistently
    rebuilt all the time, so never have a chance to get too horribly
    out of date?

- Future bug with rejection: methinks the bound computation needs to
  be able to handle situations where the state is not constant across
  re-evaluations (which, in fact, it typically won't be?).

- Using rdb-propagate-constraints! has a bug: the propagation reduces
  the number of unconstrained random choices in the original trace,
  but is not remembered and therefore not applied to the proposed
  trace.  This creates a false correction to the acceptance ratio,
  which at least slows convergence and may lead to wrong answers in
  more sophisticated cases than the current test suite.

  - This bug is less severe than one might think, because if the
    proposal trace commits, the set of constraints from the old trace
    is retained, so, in simple cases, the resulting trace ends up with
    the correct constraint set.

- [Duplicate] There is almost certainly a severe bug in the addressing
  scheme, involving applications of non-constant compound procedures,
  but I haven't been bitten by it yet.

- Mystery bug: "atomically" breaks the collapsed-beta-bernoulli test
  when I replace the trace-in form with it, even though they are
  supposed to be equivalent.

- Is the same-operators? comparison coarse enough to allow all the
  cases I would want?

- Currently, observations do not enforce the constancy of the
  observation model.  This can cause trouble at least with ergodicity
  of the resimulation Markov chain.  Adding the requirement is also
  problematic, because e.g. foreign uncollapsed procedures would not
  register as constant, even though they actually do have fixed base
  measure.

  - However, adding the requirement may be less onerous in v1 than
    v0.2, because of other flexibilities.

- The way I wrote rebuild-rdb and mcmc-step, it never actually garbage
  collects old addresses from the trace, which has the two funny
  effects that
  a) Old choices stick around and may come back
  b) Proposals to shadow choices are made (and always accepted
     because there is no likelihood)

- Also, grep the source for CONSIDER to find issues calling for
  thought.

- When hunting mystery bugs, could grep the source for ASSUME to check
  for surprising invariants the code requires.

- TODO comments should be relatively ignorable local improvements now.
