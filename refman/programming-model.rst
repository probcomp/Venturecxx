Programming Model
-----------------

The top-level VentureScript program is much like a (randomized)
program in any other high-level programming language, with one
critical difference: It may

- use `assume` operations to build up an
  arbitrarily complex probabilistic model, as the space of execution
  histories of a sub-program, called the `model program`;

- use `observe` operations
  to specify conditions that program's execution history
  should satisfy;

- use `predict` operations specify queries against that model; and

- invoke various inference operations to manipulate samples of
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

VentureScript is programmed in a JavaScript-inspired concrete syntax.
In addition, VentureScript has a Lisp-like written representation for
abstract syntax trees, and also accepts programs written in that (with
the `--abstract-syntax` flag).  As of the present writing, the system
will report most errors in the abstract syntax, and you may find some
definitions and examples in this manual written that way as well.
