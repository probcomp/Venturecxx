Broadly, the archiceture of Venture v1 is a "normal" Scheme-like
interpreter with swappable traces, which offers a hook by which traces
can observe and influence interpretation.

More specifically, it's a run-of-the-mill eval-apply interpreter,
except

- It maintains additional interpretation context, namely the current
  "writable" trace and a set of current "readable" traces.

- The environment maps symbols to "addresses" rather than values.

- The traces are expected to map the addresses of previously evaluated
  expressions to their values

- At every (sub-)expression evaluation, the interpreter invokes a hook
  on the current "writable" trace, giving it the full evaluation
  context and the putative result, wherewith the trace can do what it
  pleases, including changing the result.

- There is a special form for changing the current "writable" trace,
  including changing its type.

- There is a standard library of traces that are useful for various
  purposes; since Venture is a probabilisitic programming language,
  the purposes in question are tracing the execution of various
  models, and permitting various kinds of inference algorithms to run
  on them.

This particular breakdown was motivated by the idea that the actual
interpreter of a programming language tends to be very difficult to
change; so it should be responsible for as little as possible, and
that which does go into it should be as perfect as possible.

A trace, on the other hand, is more swappable than the interpreter:

- The existence of a trace in the standard library permits some to use
  it without requiring others to.

- Multiple traces can be used in different parts of an overall
  program, allowing experimentation and incremental migration.

- There does not seem to be a "perfect" trace:

  - There seem to be tradeoffs among different styles of trace, on the
    dimension of costs imposed vs algorithms enabled (and the
    asymptotic scaling thereof)

  - Even within a style, there seem to be local tradeoffs, choices,
    and variants, such that it is not clear which to choose.

Q: What's with the metadata facility?

A: Different inference techniques may want to know all sorts of
interesting information about a stochastic process.  For example,
M-H-based inference techniques tend to be interested in assessing the
probability (density) of a given output for given inputs; rejection
sampling additionally needs an upper bound on that density; gradient
methods want derivatives (of simulators and assessors); enumeration or
quadrature methods want to be able to systematically traverse the
output space of a procedure; and given how long this list already is,
it's almost certainly actually an open set.  So a generic metadata
facility seems to be the only way to permit the system to implement
various inference algorithms, without precommitting to a particular
list of metadata (and contracts for it).

We had considered declaring assessors special and baking support for
them into the system, but that turned out not to be necessary.

Q: From the perspective of a trace (author), what is the interpreter
actually good for?  After all, since a trace gets the full context, it
can easily reimplement the whole thing, adjusting it as desired for it
purposes.

A: Several things:

- The default evaluation behavior, which will presumably be good for
  many purposes

- Interoperability with the existing library of traces, in the sense
  of being able to delegate parts of the program to them

- Permission to focus on only the part of the program which one's
  trace is actually given to trace, and therefore the ability to make
  one's trace usable by other traces (this is interoprability in the
  other sense)

Q: Will this architecture hold up when (constant factor) performance
starts to become an issue?

A: Well, don't know yet, but maybe.  We expect that:

- In the common case, the trace to use for any given piece of code
  will be statically apparent, effectively allowing the compiler to
  inline the known tracing behavior into the interpreter hook and
  proceed from there.

- Custom trace types will be written rarely enough that demanding
  compiler plugins to achieve good performance will be acceptable.

  - There may also be some relatively generic plugins along the lines
    of "if your trace obeys such and so, I can do this and this for
    you"

- In the beginning, probabilistic programs will be short enough that
  whole-program compilation will be feasible.
