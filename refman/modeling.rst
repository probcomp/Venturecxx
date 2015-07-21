Modeling Syntax Reference
=========================

Introduction
------------

The VentureScript modeling language is the language in which model
expressions, namely the arguments to the `assume`, `observe`, and
`predict` instructions are written.  The VentureScript inference language is
the same language, but with a few additional predefined procedures and
special forms.

The VentureScript modeling language is a pure-functional dialect of
JavaScript.  The major differences from JavaScript are

- No mutation (only inference can effect mutation, and that only in a
  restricted way)

- A spare set of predefined procedures and syntactic constructs

- Several constructs relating specifically to probabilistic modeling
  or functional programming

- Predefined procedures for random choices according to various
  distributions.

Special Forms
-------------

The special forms in VenChurch are as follows:

- `(quote datum)`: Literal data.

  The datum must be a Venture expression.
  As in Scheme, a `quote` form returns a representation of the given
  expression as Venture data structures.

.. include:: model-macros.gen

In addition, macros intended for the inference programming language
are (as of this writing) expanded in expressions of the modeling
language as well.  The results are generally not useful, so it's
appropriate to treat those as reserved words when writing models:

- do, begin, call_back, collect, assume, observe, predict,
  force, sample, sample_all

Built-in Procedures
-------------------

The following modeling procedures are built in to Venture (as of the
generation date of this manual):

.. include:: modeling.gen

You can ask your Venture installation for a current version of this
list by running the ``vendoc`` program (with no arguments).

Built-in Helpers
----------------

- `true`: The boolean True value.

- `false`: The boolean False value.
