One can always express coupled procedures in a pure language by
explicit state passing: instead of a maker of coupled procedures of
type

  maker :: hypers -> (args -> Coupled out)

have

  maker :: hypers -> (state, args -> state -> IID (out, state))

Note the function is now iid (conditioned on the state given as
input).  Reproducing a sequence of applications of the coupled
procedure requires explicitly threading the state.

Assessing this version is a bit funny, because the typical case is
assessable on the 'out' output, but deterministic (conditioned on out)
on the 'state' output.  The arrangement can also be modeled as

  maker :: hypers -> (state, args -> state -> IID out
                     , args -> state -> out -> state))

where I have demanded the incorporator function be deterministic,
as is typical.  My RandomDB effectively demands this factoring
from assessable coupled procedures, but takes care of the state
threading automatically.

Anyway, modeling coupling like this produces a chain of determinisitic
dependencies from one widget representing an application of the
original coupled SP to the next through all of them.  This is a mere
curiosity for maximal re-execution scaffolds, but a minimal
re-execution scaffold can be made much smaller if we demand the state
changes be invertible and exposed to the inference program.

What do you call it when an HMM's transition operator is actually
deterministic?  The states are still hidden, and they still obey the
Markov property that the next directly depends only on the previous,
and it's still a model, but it just doesn't feel the same, somehow.
