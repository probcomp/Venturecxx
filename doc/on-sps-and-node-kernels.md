Thoughts on Venture's SP and kernel interface
Date: circa mid-late 2014

Venture currently has three points of unbounded extensibility:
- scaffold-kernels (which the code calls gkernels) which are fed to
  mix-mh over scaffolds to make a global transition operator
  - Other transition operators are possible in principle but we don't
    have any
- node-kernels (which the code calls lkernels) which propose changes
  to the values of individual nodes (and individual auxes)
- (P)SPs, which define modeling primitives

The reason we make a distinction between node-kernels and
scaffold-kernels is the regen-detach boundary: We claim that regen and
detach capture the structure of walking over the trace graph, so are
worth implementing by us.  Regen and detach on a given scaffold are
parameterized by node-kernels, and called by the scaffold-kernel, to
implement the desired transition operator.  Regen and detach are also
somewhat parameterized by the information the scaffold-kernel wants,
namely gradients or log density bounds. [1]

Node-kernels (counting resimulation from the prior as a node-kernel)
are the real things that modify the trace, and report various
information to regen and detach.  (P)SPs are just data structures that
enable various node-kernels, and enable various information-gathering
modes thereof.  Node-kernels vary in what (P)SPs they apply to:
resimulation and DeterministicLKernel are quite generic, applicable to
many (P)SPs; DefaultAAALKernel is less generic; and other node-kernels
may be very specific indeed.

Some of these applicability questions can be captured in a reasonably
natural type system.  For example, Gaussian drift kernels should be
applicable, in principle, to any node that holds a 1-D continuous
variable; and DefaultAAALKernel is applicable to any node whose
operator 1) is a maker 2) makes things that support the
logDensityOfData method and 3) supports
madeSpLogDensityOfDataBound if we are doing rejection sampling.

Venture's foreign interface therefore needs to be a coherent interface
for both SPs and node-kernels, including how information gets from one
to another, and how node-kernels are selected for addition to
scaffolds.  Also, we need to rationalize and tell the story for which
of the node-kernels that ship with Venture demand which (P)SP methods,
and which of the inference commands (scaffold-kernels) rely on which
node-kernels.

In this view, latent simulation requests are extra nodes to which even
the resimulation node-kernel does not apply.  The presumption is that
the author of the SP that introduced these latents also authored at
least one node-kernel that does apply to them (and presumably only to
them).

In this view, an infer instruction is not complete without a story for
which node-kernels to select for each scaffold node.  Our current
story (in Lite) seems to be pretty confused -- something like
1. If the operator of a node can AAA:
   a. ask it for a kernel tagged "getAAALKernel" and use that;
   b. if it doesn't have one, use the DefaultAAALKernel;
   c. if that is not applicable crash.
2. If we are running Meanfield, ask the operator for a kernel
   tagged "getVariationalLKernel", the default implementation of which
   is DefaultVariationalLKernel.
3. If the scaffold-kernel said "I accept delta kernels" (which I think
   none of them do), ask the operator for a kernel tagged
   "getDeltaKernel"; if it doesn't have one continue.
4. If the scaffold-kernel wishes to control the value in this node,
   (e.g., enum-gibbs, hmc, slice) it does so with a
   DeterministicLKernel.
5. Otherwise use the resimulation kernel.
6. Every time an SP is made, ask it for a kernel tagged "hasAEKernel"
   and store all such kernels.  Execute all such kernels
   unconditionally after every transition of any other infer
   operation.
This needs improvement.

Am I right?  Did I miss anything?

[1] The bound is not actually computed by calling regen or detach
right now, but by a custom recursion.  Perhaps the actual graph
walking needs to be abstracted from the things one might wish to do
during it, like taking values out of nodes or putting them back in.
