Venture Stan Integration
========================

Broadly, the (first) goal of Venture-Stan integration is to be able to
use Stan from Venture, reflecting a Stan model as a stochastic
procedure that can participate in a Venture model.

I made two relatively arbitrary architectural choices in drafting the
first version of the integration, which I state here as axioms but
will revisit later:

1. The Stan model and the Stan engine are treated as black boxes, with
   no attempt at parsing, interpretation, or off-API control.

2. The Stan model is mirrored in Venture as a stochastic procedure (SP)
   with a semantic output, which is simulable and constrainable.

Architecture
------------

The entry point to Stan integration is the Venture SP `make_van_stan`.
`make_van_stan` accepts
- a string representing a Stan model,
- a description of the Stan names and Venture types of the inputs, and
- a description of the Stan name and Venture type of the output, and
- returns a Venture SP representing the model.

The SP returned by `make_van_stan` accepts inputs of the specified
types and returns an output of the specified type, which can be
constrained (and therefore can absorb changes to its inputs).

- The parameters (in Stan's sense) of the model are kept internal to
  the SP (uncollapsed), and indexed by a latent simulation request.

- Each application of the made SP is independent of all the others,
  and corresponds to a separate instance of Stan.

- Stan inference is packaged for Venture as an `AEKernel` ("AE" for
  "arbitrary ergodic") on the made SP.

Usage Requirements and Gotchas
------------------------------

- The output datum has to appear twice in the Stan model: once as a
  datum that contributes to the density defined by the model, and once
  as a generated quantity (presumably with a different name; both
  names need to given to Venture).  It is up to the user to make sure
  that the density and the sampler define the same probability
  distribution (conditioned on the inputs and the Stan parameters).

- The Stan model must be written without sampling statements, using
  only `increment_log_prob` statements.  This is because sampling
  statements implicitly drop terms of the posterior density that do
  not depend on the parameters, but Venture needs those to be able to
  evaluate acceptance ratios for proposals that move the input data.
  (See [here](https://groups.google.com/forum/#!topic/stan-users/wFr0rYMo0oM).)

- The latent parameters are initialized by Stan's native
  initialization procedure, not sampled from any prior.  Consequently,
  forward sampling of the output follows a weird distribution, which
  does not correspond to anything for which a density is available.

- Forward simulation of the output even conditioned on the parameters
  follows a somewhat wonky distribution, because there is actually no
  way that I discovered and that works in pystan to ask Stan to
  generate simulated quantities without doing any inference on the
  latent parameters.  See Issue #TODO.

Alternatives not Attempted
--------------------------

1. Additional goal of being able to write component distributions for
   Stan in VentureScript.

2. Alternative embedding of a Stan model as an SP that computes its
   (conditional) likelihood, or an `observe`-like macro or instruction
   that adds the Stan model as a factor.

   - Pro: More natural from Stan's point of view; no need to write a
     sampler for the "output" variable(s).

   - Pro: Initialization distribution of the parameters is not a
     problem.

   - Con: Violates Venture's expectation that everything is usefully
     forward samplable.

   - Con: No way to condition anything on the latent parameters;
     equivalently, no way to expose Stan's "generated quantities"
     facility.

3. Deeper integration, involving parsing and/or generating (parts of)
   the Stan model.  The major cost is writing and maintaining such
   parsers or generators, and any needed semantic mappings between
   Stan's primitives and means of composition and Venture's.  The
   potential benefits are:

   - Automatically converting sampling statements into
     `increment_log_prob` statements to get the true posterior.

   - Alternately, could evaluating M-H ratios for proposals to the
     inputs in Venture without Stan.

   - Sampling the parameters from the prior rather than from Stan's
     initialization distribution, thus forcing Stan to sample the
     output from the prior.

   - Sampling the output from the prior in Venture, without Stan.

     - Eliminates the generated quantity code duplication.

   - Computing the input-output spec automatically from the model, or
     generating parts of the model automatically from the input-output
     spec.

     - Eliminates code duplication between the Stan data block and the
       name and type declarations that need to be passed to
       `make_ven_stan`.

   - Computing an entire Stan model by inspecting an HMC-appropriate
     fragment of a Venture trace.

   - Conversely, constructing a Venture trace fragment corresponding
     to the interior of a Stan model, and perhaps applying other
     inference tactics to it
