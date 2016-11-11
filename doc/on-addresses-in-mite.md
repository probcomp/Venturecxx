I decided at one point that it would be nice if Mite addresses were
unique across as well as within traces.

Why did I decide this?  I wanted the Mite evaluator to be able to read
values held in environments whose evaluation was traced in a different
trace from the present one.  Since the environments were keyed by
address, that made it necessary to make sure that the addressed were
unique.

This decision caused the problem that I now need two distinct notions.
One is the notion of a fully specified address, which knows the trace
it is part of; this can serve as the key in an enviornment.  But I
also need a notion of "address pattern", or "address relative to the
top of an unknown trace".  Why is this notion needed?  Because we want
to be able to write a phrase like "/4/1" and interpret it relative to
any trace that comes in (as the first subexpression of the fourth
toplevel expression recorded in this trace).

I chose to implement that as follows.  The existing `Address` class
hierarchy in `venture.mite.addresses` represents a trace-specific
address.  This is achieved by adding a field to the `DirectiveAddress`
class to hold the integer id of the intended trace.  These ids are
meant to be unique across traces but otherwise unstructured.

A "trace-relative address" is represented by an object in the same
class hierarchy that has `None` in the place of the trace id.  The
meaning of `None` there is "any".  The operation
`interpret_address_in_trace` replaces all such `None` entries in
a given address with the desired trace id.

I considered an alternative isomorphic representation the same idea,
namely to make the address hierarchy represent trace-agnostic
addresses and key environments by pairs of `Address` and trace id.  In
effect, `interpret_address_in_trace` becomes `cons`.  I decided that
this option was more awkward.

Open problems:

- Trace copying currently copies the trace ids too, making them not
  actually unique.  Unfortunately, if we were to change a trace's id
  when copying it, we would need to traverse all of the addresses
  stored in all of its environments in order to re-key them.  This is
  not actually any more expensive than the copy operation in the first
  place, but is lots of nasty code.  We have not been bitten by this
  problem yet because copied traces do not appear in each other's
  lexical environments.

- Regenerations that occur in an outer trace may not properly
  propagate while evaluating in the inner trace, because (I think) the
  "XXX hack to propagate regenerated global bindings" would not work
  (I think).
