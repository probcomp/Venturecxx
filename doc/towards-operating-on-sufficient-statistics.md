Towards Operating on Sufficient Statistics
Date: mid-late 2014

Example use-case: observing 100 even flips of a collapsed coin in
o(100) work:

```
assume flip_coin (make_beta_bernoulli 1 1)
observe ((bulk flip_coin)) <list>(50, 50)
predict (flip_coin)
```

Step 0:

A full histogram of counts of argument-value pairs is always a
sufficient statistic for any SP, by exchangeability.  There is a very
interesting question of homomorphisms to smaller Abelian groups which
I will take up later; but for now when I say "sufficient statistics"
think "counts".

Step 1:

The Venture SP interface is already compatible with operating directly
on reified sufficient statistics rather than individuals.  For
instance, nothing prevents us from defining `(make_bulk_beta_bernoulli y n)`
which returns a procedure `bulk_flip` of type `<count> -> (<count>, <count>)`
where `(bulk_flip n)` returns a 2-tuple of the number
of heads and tails that come from flipping an appropriate coin `n` times,
and applications of `bulk_flip` are exchangeably coupled to each other.

There is one subtlety with this design pattern, which is that the bulk
procedure accepts a count of how many values to produce sufficient
statistics for (which, actually, is the sufficient statistic of the
set of individuals the thing is being notionally invoked on), because
`simulate` and `enumerateValues` need it.  This count is, however, a
deterministic consequence of the output, so `logDensity`, `incorporate`,
and `unincorporate` do not need to read it.  It would be nice if we
could make a coherent design that allows such a bulk procedure to be
observed without producing contradictions if the observed statistics
differ from the input count.

Step 2:

It would be interesting to be able to relate bulk procedures with
individual procedures.  To wit, there should be a higher-order
procedure named "bulk" (or something like that) that converts
procedures operating at the level of individuals to procedures
operating at the level of sufficient statistics _that remain
exchangeably coupled_.

In the above example, `(bulk (make_beta_bernoulli y n))` should be the
same as `(make_bulk_beta_bernoulli y n)`.  The bulk version should share
the aux with the non-bulk version (perhaps by reference) so that

```
assume flip_coin (make_beta_bernoulli 1 1)
observe ((bulk flip_coin)) <list>(50, 50)
predict (flip_coin)
``

works.

For builtins, "bulk" can be implemented by extending the SP interface
with an additional method named something like "associated bulk
procedure" and just having "bulk" call it.  The default case would be
to implement all the methods of the bulk version by just repeated
application of corresponding methods of the base (for sufficient
statistics that are histograms of args-value pairs).

Issues:

- AAA should just work in the presence of this

- It would be nice to also have a procedure called "unbulk" or
  "individualize" that extracts the underlying individual procedure
  from a bulk procedure.  For procedures made by bulking, this should
  literally just extract.  For "natively-bulk" procedures, this can be
  done by calling the bulk procedure on a histogram of size 1.

  - In fact, "natively-bulk" could be the default; and we may not even
    need the "bulk" combinator (or just have it be "extract").

- We have a choice about the meaning of bulking a bulk procedure.  The
  "right thing" is histograms over sets of possible histograms, but
  there is a natural join operation collapsing that to just
  histograms.  We could choose either to offer that operation as a
  separate one, or apply it automatically (in which case, I think bulk
  becomes idempotent).

- Do we want to bulk SPs or PSPs?
  - Does it make sense to bulk PSPs that make requests?
  - Do we want to restrict bulking to just null-requesting SPs?

- What's the right story for bulking procedures that are themselves
  higher order?

- This proposal is orthogonal to bulk_observe.  bulk_observing a bulk
  procedure is probably the complete solution to the "observe a
  dataset" problem.

- The set of SPs that admit sufficient statistics is larger than we
  are currently taking advantage of.

Step 3: Other Abelian groups

One of the potential wins of the idea of sufficient statistics is that
sometimes the bulk operations one is interested in factor through a
homomorphism of Abelian groups from the free Abelian group on
args-output pairs to a group G with a smaller representation (for
example, the sum of a bunch of continuous data points).

At the moment, we take advantage of this phenomenon by storing only
elements of G in the auxes of our individual procedures.  It would be
nice to also reduce the representations of various sufficient
statistics that SPs operate on.  Unfortunately, I don't think this can
be done completely automatically, because different SPs imply
different operations, so the choice of what the group G is cannot be
made by examining just one SP.  So we would want a mechanism by which
the programmer can select the group (by knowing what SPs are going to
do what with the data) and getting versions of SPs that operate on
that representation.  Second problem: the default implementation by
looping only works for the free group.

The grungy way to do that is to make the names of all the groups for
all the variables an SP interacts with (input and output) be part of
the name of the SP, and just producing custom code for every desired
combination.  It may be possible to do one step better by defining
group homomorphisms explicitly, and automatically composing them in
the proper directions, to build type-correct implementations from
fewer custom codes.
- Something that may help here would be a notion of an SP dispatching
  on the group in which its output is requested, to choose the best
  algorithm.

Step 4: Compound procedures

One possible interesting treatment of compound procedures would be to
look for a source-to-source transformation of their body that
bulkifies everything appropriately.  I have no clue how to start this.

A less ambitious version would be to first define a special form
called, say, mu which makes collapsed compounds (by the user supplying
the homomorphism from the free Abelian group in some form, and
supplying code that implements the exchangeable coupling given an
element of the desired group).  Then the above ideas of bulkification
apply.

----------------------------------------------------------------------

More specific notes from before I was clear on the role of different
Abelian groups.  These particular notes are written assuming that the
inputs of the SP are represented as a histogram (with one column!) and
the SP itself chooses the group representing the outputs.

For any given type of aux, define a wrapper class
```
class BulkPSP(PSP):
  def __init__(self, internal_psp):
    self.internal = internal_psp
  ...
```
which represents a PSP whose output is a reified representation of the
sufficient statistics stored in the aux of the internal psp.  The aux
of `BulkPSP` needs to store a pointer to the aux of the internal one
(through which it can mutate the latter).

Specifically, for a PSP `p` of type
```
p :: Prod_i A_i -> B
```
which maintains sufficient statistics of type `G`, the bulk has type
```
BulkPSP(p) :: Count x Prod_i A_i -> G
```

The interface of the bulk PSP is

- `BulkPSP.incorporate(value, args)` interprets the value (of type `G`)
  as a set of sufficient statistics for applications of the internal
  psp to the given arguments (ignoring the given count), and adds them
  to the latter's aux.

- `BulkPSP.unincorporate(value, args)` does the reverse.

- `BulkPSP.logDensity(value, args)` interprets the value the same way
  as `incorporate`, and computes the density of getting those statistics
  by applying the internal_psp the correct number of times. [*]

- `BulkPSP.simulate(args)` returns a reification (of type `G`) of a
  set of sufficient statistics for sampling the internal psp, the
  given count number of times, on the given arguments.

- `BulkPSP.enumerateValues(args)`, if appropriate, returns a list of
  all possible sets of sufficient statistics (per `BulkPSP.simulate`)
  corresponding to the given count.

[*] I believe that `logDensity` can still ignore the given count,
because if the number of applications matters to the answer, then it
should be deducible from the set of sufficient statistics that are the
value.

Example: `binomial` is almost the BulkPSP of the coin-flipping procedure
that `make_beta_bernoulli` returns, except that it returns only the
number of heads (without the number of tails), and it does not adjust
any other procedure's aux (also, binomial is uncollapsed).
