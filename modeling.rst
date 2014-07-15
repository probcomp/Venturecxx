Modeling Syntax Reference (VenChurch)
=====================================

Introduction
------------

The Venture modeling language is the language in which model
expressions, namely the arguments to the `assume`, `observe`, and
`predict` instructions are written.  The Venture inference language is
the same language, but with a few additional predefined names,
procedures, and special forms.

The VenChurch surface syntax for the Venture modeling language is a
pure-functional dialect of Scheme, which puts it in the Lisp family of
programming languages.  The major differences from Scheme are

- No mutation (only inference can effect mutation, and that only in a
  restricted way)

- A spare set of predefined procedures and special forms

- Predefined procedures for random choices according to various
  distributions.

Special Forms
-------------

The special forms in VenChurch are as follows:

- `(lambda (param ...) body)`: Construct a procedure.

  The formal parameters must be Venture symbols.
  The body must be a Venture expression.
  The semantics are as in Scheme or Church.  Unlike Scheme, the body
  must be a single expression, and creation of variable arity
  procedures is not supported.

- `(if predicate consequent alternate)`: Branch control.

  The predicate, consequent, and alternate must be Venture expressions.

- `(and exp1 exp2)`: Short-circuiting and.

- `(or exp1 exp2)`: Short-circuiting or.

- `(let ((param exp) ...) body)`: Evaluation with local scope.

  Each parameter must be a Venture symbol.
  Each exp must be a Venture expression.
  The body must be a Venture expression.
  The semantics are as Scheme's `let*`: each `exp` is evaluated in turn,
  its result is bound to the `param`, and made available to subsequent
  `exp` s and the `body`.

- `(quote datum)`: Literal data.

  The datum must be a Venture expression.
  As in Scheme, a `quote` form returns a representation of the given
  expression as Venture data structures.
