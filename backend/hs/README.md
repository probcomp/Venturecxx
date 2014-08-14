As of this writing, this directory contains two distinct artifacts.

HsVenture
---------

HsVenture is a partial Haskell implementation of the Venture language
as I understood it right around the 0.1.x releases (the bulk of
development occurred between 11/21/13 and 12/16/13, with work toward a
server understanding the Venture wire protocol occurring
4/5/14-4/9/14, and then 5/13/14).

The library in the cabal file, as well as the test suite "tests" and
the executable "venture-server", are HsVenture.  This covers all the
modules here except `TraceView.hs`.  HsVenture runs, and passes a tiny
sanity check suite (which includes some tests of statistical
correctness).

The only substantial architectural difference between HsVenture and
Ventures 0.1.x and 0.2 is that the Traces in HsVenture are
pure-functional.  This should make particle methods much easier to
implement, and keep the code for operating on a Trace much simpler and
easier to understand; at the cost of some additional complexity
plumbing Traces, and at the threat that the extra layer of indirection
will come back and bite the program's performance.

Potential uses for HsVenture
============================

- Expository implementation (this would require some considerable
  massaging and beautifying)
- Testbed for clearly stating and checking implementation invariants
- Quasi-independent Venture implementation for cross-checking
  (especially HMC, which in HsVenture should be implementable with a
  good third-party AD library instead of by hand)

It would be a Simple Matter of Programming to develop HsVenture into a
full implementation of Venture 0.2.  The punch list for that job, in
broad strokes, is:

- Extend the definition of Value to include ReifiedTrace as an option
- Refactor inference programming to run the inference program in a new
  Trace, like the Engine in 0.2 does (and add an Infer Directive)
- Finish the server, so that the test suite of 0.2 can execute against
  HsVenture over a TCP connection
- Implement a few more inference primitives, like particle gibbs,
  slice sampling, and HMC
- Round out the set of built-in Venture-level value types to match 0.2
- Round out the set of built-in SPs
- Implement the rest of "children absorb at applications"
    - Collecting statistics works
    - Exchangeably coupled collapsed models work
    - Implement Gibbs steps for uncollapsed models
    - Implement absorbing hyperparameter changes at collapsed models
- Implement SMC-style with a weighted set of traces
- Implement separate tracking of the constraints that observations
  impose and the appropriate model of propagating them
- Debug thoroughly and pass the 0.2 test suite
- Does anything actually require detach-regen order symmetry?  It may
  be necessary to rewrite detach to enforce it (do the
  insertion-ordered sets already do that?).
- [Techincally] Add latent simulation requests, latent simulation
  kernels, and local transition kernels, none of which are widely
  used or understood in Venture 0.2
    - Refactoring: with local kernels, all parts of regen, eval,
      evalRequests, and detach may produce contributions to the
      weight.
- [Optional] Use the Haskell-C interface to be able to call Python
  Venture SPs
- [Optional] Use the Haskell-C interface to allow the Python stack to
  run HsVenture in-process (presumably by overriding CoreSivm or
  the stack's Engine)

