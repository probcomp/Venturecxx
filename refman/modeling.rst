Modeling Syntax Reference (VenChurch)
=====================================

Introduction
------------

The Venture modeling language is the language in which model
expressions, namely the arguments to the `assume`, `observe`, and
`predict` instructions are written.  The Venture inference language is
the same language, but with a few additional predefined procedures and
special forms.

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

- `(quote datum)`: Literal data.

  The datum must be a Venture expression.
  As in Scheme, a `quote` form returns a representation of the given
  expression as Venture data structures.

.. include:: model-macros.gen

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
