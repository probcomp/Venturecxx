VenStan: Experimental Stan Integration
======================================

VentureScript programs may interoperate with models written in the
popular probabilistic programming system Stan_.  The interface is
experimental, but suffices to build joint models where, for example,
one may use Stan's NUTS sampler to make transitions over some block of
continuous variables and VentureScript's native enumerative Gibbs over
a collection of discrete ones.

For a complete (if contrived) example, see
``examples/venstan/normal_normal.vnts`` in the Venture distribution.

Architecture
------------

The entry point to Stan integration is the Venture SP `make_ven_stan`.
`make_ven_stan` accepts

- a string representing a Stan model,
- a description of the Stan names and Venture types of the inputs, and
- a description of the Stan name and Venture type of the output, and
- returns a Venture SP representing the model.

The SP returned by `make_ven_stan` accepts inputs of the specified
types and returns an output of the specified type, which can be
constrained (and therefore can absorb changes to its inputs).

- The parameters (in Stan's sense) of the model are kept internal to
  the SP (uncollapsed), and indexed by a latent simulation request.

- Each application of the made SP is independent of all the others,
  and corresponds to a separate instance of Stan.

- Stan inference is packaged for Venture as an ``AEKernel`` ("AE" for
  "arbitrary ergodic") on the made SP.

Usage Requirements and Gotchas
------------------------------

- The output datum has to appear twice in the Stan model: once as a
  datum that contributes to the density defined by the model, and once
  as a generated quantity (presumably with a different name; both
  names need to given to Venture).  This is necessary because the
  VentureScript stochastic procedure is expected to be able to either
  forward-simulate or condition on its return value -- those
  operations are expressed as generated quantities and input data,
  respectively, in Stan.

  It is up to the user to make sure that the density and the
  sampler define the same probability distribution (conditioned on the
  inputs and the Stan parameters).

- The Stan model must be written without sampling statements, using
  only `increment_log_prob` statements.  This is because sampling
  statements implicitly drop terms of the posterior density that do
  not depend on the parameters, but Venture needs those to be able to
  evaluate acceptance ratios for proposals that move the input data.
  (See here_.)

- The latent parameters are initialized by Stan's native
  initialization procedure, not sampled from any prior.  Consequently,
  forward sampling of the output follows a weird distribution, which
  does not correspond to anything for which a density is available.

Reference
---------

To use VenStan, is it necessary to have pystan_ installed, and then to
run::

    load_plugin("venstan.py")

This makes the `make_ven_stan` procedure available.

.. function:: make_ven_stan(<stan_model> : string, <list of input specs>, <list of output specs>[, <cache dir> :string])

   ``make_ven_stan`` will return a stochastic procedure each of whose
   applications will be one instantiation of the Stan model.

   An input spec is a list of two elements: The Stan name of an input
   and the VentureScript type of that input.  The returned procedure
   will accept inputs in that order, and map them to Stan data items
   of those names.

   An output spec is a list of three required elements followed by any
   number of optional size specifications.  The first element is the
   Stan name of the generated quantity representing the output.  The
   second element is the Stan name of the corresponding input.  The
   third element is the VentureScript type of that value.  If the type
   is an array (of whatever dimension), that many additional elements
   are required which are strings giving Python expressions that
   evaluate to the sizes of each dimension of that array.  These may
   refer to the value of other inputs by their Stan names.

   For example::

        assume stan_prog = "
        data {
          int N;
          real y[N];
        }
        ...
        generated quantities {
          real y_out[N];
          ...
        }";
        assume inputs = quote("N"("Int")());
        assume c_outputs = quote("y_out"("y", "UArray(Number)", "N")());
        assume stan_sp = make_ven_stan(stan_prog, inputs, c_outputs);

    Now ``stan_sp`` is a one-input one-output VentureScript procedure
    that represents the distribution on ``y`` given ``N``, taking any
    parameters of the Stan model as latent variables.  Here ``y_out``
    and ``y`` are a corresponding output-input pair.  Venture
    synthesizes an initial ``y`` to bootstrap forward simulation
    (which is why the sizes of any arrays need to be supplied).

    Note: VenStan can only handle one output from Stan at present.  We
    require a (one-element) list of output specs for forward
    compatibility.

.. _Stan: http://mc-stan.org
.. _here: https://groups.google.com/forum/#!topic/stan-users/wFr0rYMo0oM
.. _pystan: http://mc-stan.org/interfaces/pystan.html
