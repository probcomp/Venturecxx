Venture Foreign SP Interface
============================

Interface
---------

Foreign SPs can be registered in Venture via the bind_foreign_sp call:

    from venture.shortcuts import make_church_prime_ripl
    from venture.lite.sp_help import binaryNum
    v = make_church_prime_ripl()
    v.bind_foreign_sp('f', binaryNum(lambda x, y: 10*x + y))
    v.sample('(f 2 5)')

`bind_foreign_sp` takes a `venture.lite.sp.VentureSP` object and binds
it as a constant in the global environment.

In the Lite backend, the SP object is passed through in the
straightforward way, and supports the full SP interface.

Wrapping
--------

For the Puma backend, there is a translation layer consisting of a
pair of wrappers that marshall the arguments and return values of SPs
between backends. Currently, the translation layer is incomplete; not
all methods of the SP interface are supported. However, simple
deterministic and stochastic SPs should work.

The following is a list of the functionality that is currently *not*
supported by the translation layer:

* Nontrivial canAbsorb methods (i.e. SPs that absorb from some parent
  nodes but not others)
* SP auxiliary storage (SPAuxes)
* First-class functions as arguments
* First-class environments
* Explicit simulation requests (ESRs)
* Latent simulation requests (LSRs)
* Arbitrary ergodic kernels (AEKernels)
* Gradients
