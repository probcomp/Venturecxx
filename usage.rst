Usage
-----

Venture can be invoked in two styles: as a standalone language, and as
a Python library.

Interactive console::

    $ venture
    >>> assume x (normal 0 1)
    >>> observe (normal x 1) 2

Source file::

    $ cat prog.vnt
    [assume x (normal 0 1)]
    [observe (normal x 1) 2]
    $ venture puma -f prog.vnt

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
        [observe (normal x 1) 2]
    """)

The expressive power of the two methods is equivalent, because the
standalone language can be extended with plugins and callbacks written
in Python, which can then manipulate the Venture system
programmatically.

There are two syntaxes for expressions: Venchurch
(Scheme/Church-like) and VentureScript (Javascript-like). The
reference manual will use the Venchurch syntax.

