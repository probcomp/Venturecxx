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

The results are now documented in the reference manual:
http://probcomp.csail.mit.edu/venture/edge/reference/venstan.html

Additional Gotchas
------------------

(that I didn't want to advertise in the reference manual)

- Forward simulation of the output even conditioned on the parameters
  follows a somewhat wonky distribution, because there is actually no
  way that I discovered and that works in pystan to ask Stan to
  generate simulated quantities without doing any inference on the
  latent parameters.  See [Issue #253](https://github.com/probcomp/Venturecxx/issues/253).

- There are tons of outstanding bugs and infelicities even at this
  level of integration.  They are tracked in the [Stan integration works
  well](https://github.com/probcomp/Venturecxx/milestones/Stan integration works well)
  milestone.

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
