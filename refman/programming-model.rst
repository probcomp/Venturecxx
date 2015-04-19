Programming Model
-----------------

VentureScript programs consist of a series of instructions which are
executed by the Venture SIVM (Stochastic Inference Virtual
Machine).  These instructions

- Build up a generative model for some phenomenon of interest
  (`assume`),

- Include events on which that model is to be conditioned (`observe`),

- Specify queries against that model (`predict`),

- Invoke inference to explore the space of explanations of the events
  that the model judges as plausible (`infer`), and

- Preform various additional and supporting functions (the others).

The top-level VentureScript program is much like a (randomized)
program in any other high-level programming language, with one
critical difference: It may use `assume` instructions to build up an
arbitrarily complex probabilistic model, as the space of execution
histories of a sub-program, called the `model program`; use `observe`
instructions to specify conditions that program's execution history
should satisfy; and use `infer` instructions to manipulate samples of
that execution history to evolve them, in distribution, perhaps toward
the Bayesian posterior conditioned on the observations (or perhaps
not, depending on the programmer's wishes).

When we wish to distinguish it from the model program, we refer to the
toplevel program as the `inference program`.  The programming language
available to the model program, the `model language`, amounts to a
slightly restricted subset of the full VentureScript language, which
we also call the `inference language`.

For those readers for whom this is helpful, you can think of the
inference program as being run in the ``State ModelHistory`` monad
(though, more like ``ST`` with a single implicit ``STRef
ModelHistory``, because the system's state is actually mutated
underneath).  There are ``do``, ``bind``, and ``return``, as one would
expect, except that they are specialized to this one monad.

There are two syntaxes for expressions: Venchurch
(Scheme/Church-like) and VentureScript (Javascript-like). The
reference manual will use the Venchurch syntax.
