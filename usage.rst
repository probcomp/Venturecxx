Usage
-----

Venture can be invoked in two styles: in the interactive console, and
as a Python library.

Interactive console::

    $ venture
    >>> assume x (normal 0 1)
    >>> observe (normal x 1) 2

Python library::

    from venture.shortcuts import *
    v = make_church_prime_ripl()
    v.assume("x", "(normal 0 1)")
    v.observe("(normal x 1)", 2)

Python library (batch invocation)::

    import venture.shortcuts as s
    v = s.Puma().make_church_prime_ripl()
    v.execute_program("""
        [assume x (normal 0 1)]
        [observe (normal x 1) true]
    """)

There are also two syntaxes for expressions: Venchurch
(Scheme/Church-like) and VentureScript (Javascript-like). The
reference manual will use the Venchurch syntax.

