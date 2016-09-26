As of this writing, this directory contains two distinct artifacts.

HsVenture
=========

HsVenture is a partial Haskell implementation of the Venture language.

HsVenture is
- An inference dsl embedded in Haskell (cabal library, Venture.hs and
  dependencies),
- An interpreter for a standalone inference language compatible with
  VenChurch (up to available names), with
- An http server listening for commands and executing them (cabal
  executable "venture-server"), and
- A (small) test suite ("tests" in cabal)

This covers all the modules here except `TraceView.hs`.  HsVenture
runs, and passes a tiny sanity check suite (which includes some tests
of statistical correctness).

The first substantial architectural difference between HsVenture and
Ventures 0.1.x and 0.2 is that the Traces in HsVenture are
pure-functional.  This should make particle methods much easier to
implement, and keep the code for operating on a Trace much simpler and
easier to understand; at the cost of some additional complexity
plumbing Traces, and at the threat that the extra layer of indirection
will come back and bite the program's performance.

The second substantial difference is that HsVenture's inference
programming language is (meant to be) a clean embedding in Haskell
with an optional additional interpreter on top, whereas the inference
language in the late 0.2 series is explicitly interpreted.

Potential uses for HsVenture
----------------------------

- Expository implementation (this would require some considerable
  massaging and beautifying)
- Testbed for clearly stating and checking implementation invariants
- Quasi-independent Venture implementation for cross-checking
  (especially HMC, which in HsVenture should be implementable with a
  good third-party AD library instead of by hand; see non-compiling
  draft in Gradient*.hs)

Developing HsVenture into a full implementation of Venture 0.2
--------------------------------------------------------------

Would be a Simple Matter of Programming.  The punch list for that job,
in broad strokes, is:

- Finish the inference interpreter and server, so that the test suite
  of 0.2 can execute against HsVenture over a TCP connection
- Implement a few more inference primitives, like particle gibbs,
  slice sampling, and HMC
- Round out the set of built-in Venture-level value types to match 0.2
- Round out the set of built-in SPs
- Implement the rest of "children absorb at applications"
    - Collecting statistics works
    - Exchangeably coupled collapsed models work
    - Implement Gibbs steps for uncollapsed models
    - Implement absorbing hyperparameter changes at collapsed models
- Implement a library for SMC-style with a weighted set of traces
  on top of the embedding
    - Possible hack: make a typeclass for reasonable things to use to
      represent model distributions and implement it for, e.g., [Model].
- Implement separate tracking of the constraints that observations
  impose and the appropriate model of propagating them
- Debug thoroughly and pass the 0.2 test suite
- Does anything actually require detach-regen order symmetry?  It may
  be necessary to rewrite detach to enforce it (do the
  insertion-ordered sets already do that?).
- Will need to implement scopes and blocks or something somehow
- [Techincally] Add latent simulation requests and latent simulation
  kernels, neither of which are widely used or understood in Venture
  0.2
- FIXME: with local kernels, all parts of regen, eval, evalRequests,
  and detach may produce contributions to the weight.
- [Optional] Use the Haskell-C interface to be able to call Python
  Venture SPs
- [Optional] Use the Haskell-C interface to allow the Python stack to
  run HsVenture in-process (presumably by overriding CoreSivm or
  the stack's Engine)

History
-------

The initial development occurred between 11/21/13 and 12/16/13.  This
was around the 0.1.x releases; so the initial mental model stems from
that period.

Work toward a server understanding the Venture wire protocol occurred
4/5/14-4/9/14, and then 5/13/14.

Around 1/25/15-1/28/15, reworked into a mental model where the
inference language is embedded into Haskell (in the Venture module),
with an additional layer interpreting the surface syntax of Venture as
a server (whose surface was not upgraded since 5/13/14).


HS-V1
=====

HS-V1 is a draft implementation of the Venture v1 ideas in Haskell,
based on extendable PETs.  It is here because it should in principle
share substantial chunks of code with HsVenture, but currently it does
not.  The HS-V1 draft is the TraceView module, with its minor imports
from the HsVenture codebase.

HS-V1 compiles, with `undefined` stubs for a number of helper
functions.  It has never been actually run.  Development is currently
stopped on the upward funarg problem: how should the system treat
closures that are returned from extend nodes?

See [hs-v1.md](hs-v1.md) for implementation design notes.

To complete HS-V1
-----------------

One appealing and reasonably mapped-out path is to refactor the
supporting structures in HsVenture to be usable for HS-V1 as well.
To proceed along that path:

Decide what to do about upward funargs (solve the problem, ban them,
or something)

Refactor HsVenture to be compatible with HS-V1
- Relocate the basic types so they can be cyclic
- Add the stupid type variable to Value
- Add the needed extra clauses to Value, Exp, Node
    - Can react to them with "error" in the current code
- Import the new small object types from the base code in TraceView
- Notionally split lookupNode into a version that looks the thing up
  in the whole trace chain (and returns just the value, without
  permission to set?) and a version that accesses that index in the
  "current" trace, with permission to set (that would be the "nodes"
  lens).
- Introduce my own typeclass for monads that have randomness and the
  needed unique sources (addresses, sp addresses, maybe trace
  addresses if I go there)
    - I think this needs to be enough a state monad, so I can store the
      state between IO actions in the server.
- Split the really global state out of the Trace and put it into
  my new monad (namely the seeds for addresses and sp addresses)
- Add an (unused) parent_view field to Trace
- Rewrite the invariants list?

Then use the compatible HsVenture for HS-V1
- Make TraceView a type synonym for Trace and flush all the duplicated
  operations on trace views.
- Port evalRequests to the new world order
- I feel like I should be able to just reuse detach
- Port or adapt Inference to the new world order
- Add an SP named "mh" to the pantheon
- Test lightly and start playing with programs
- [Optional]: Quickcheck the data structure invariants
- If ready:
    - Adjust the grammar to emit the new expression types
    - Port Server.hs to the new way
    - Abandon the current Regen.hs, Engine.hs, and/or Venture.hs
    - Run against the extant Venture test suite (except scopes)?

Another path is to grow the existing HS-V1 into a distinct full
implementation, possibly copying and modifying chunks of code from
HsVenture as needed.
