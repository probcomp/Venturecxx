To apply a venture procedure one needs
- the procedure itself
- the (addresses of the) arguments
- the where the application is being recorded by the enclosing eval
- the trace in which the result is traced (which becomes the trace
  where the body is traced)
- the additional traces available for reading at the application site
    - which are completely ignored by application of compounds
I will call the latter three of these the "application context".

Is it possible to permit procedures that are foreign to Venture to
call Venture procedures?  Here are two ways:
A) Package up the application context of applying the foreign procedure
   itself, and make it available somehow for calling back
   - e.g. close over it in a Scheme lambda exported back to Scheme
B) Provide a trampoline (evaluation of Explicit Simulation Requests)

Pros and cons:

- A has the advantage that the foreign procedure can be written in
  direct style, interspersing callbacks into Venture with Scheme
  operations

- B has the disadvantage of imposing an inversion of control on the
  foreign procedure: its calls back to Venture have to be written in
  continuation-passing style

    - This disadvantage is mitigated by familiarity: web servers are
      already written this way, except in Racket.

    - This disadvantage may also be mitigable in Scheme by playing with
      (delimited) continuations: extend the Scheme-side api with a
      procedure named "request" that looks like it does some Venture
      crunch and returns, but actually grabs the (delimited)
      continuation of the foreign (Scheme) procedure and returns a
      request object for the trampoline.

- A has the disadvantage that the foreign procedure can capture the
  context package and do unspeakable things with it, like return it,
  pass it around, and call it somewhere else

- B has the corresponding advantage that application contexts need not
  be exposed for so simple a task as callbacks

    - We can reserve access to and understanding of the detailed
      application context interface for more serious interfacing tasks

- What is the corresponding expressiveness limitation that B imposes
  on foreign procedures?  Essentially that they cannot intentionally
  capture their dynamic application context and muck with it.  Perhaps
  that power should be left to an "expert api" regardless.

The issue of whether arguments to procedures are represented as values
or addresses seems orthogonal: one sort of foreign procedure can
expect values from Venture and emit ESRs with values in them in return
(and thus generally require much resimulation), whereas another sort
can expect operand addresses from Venture and emit ESRs with addresses
in them in return (and thus generally absorb).  The latter seems to me
analogous to what I expect the implementations of parametric
polymorphism to look like.

Decision: Implement B.

The detailed design that emerges is this:

- The baseline foreign api (expected to be used only by "experts") is
  that a foreign procedure's simulator is just called with the entire
  application context and can do with it what it pleases.

    - (cond ((foreign? oper)
             ((foreign-simulate oper) oper opand-addrs addr cur-trace read-traces))
            ...)

- We provide two combinators against that api, expected to be useful
  to "mere mortals":

    (define (scheme-procedure-over-values->v1-foreign sim)
      (make-foreign
       (lambda (oper opand-addrs addr cur-trace read-traces)
         (let ((arguments (map (lambda (o)
                                 (traces-lookup (cons cur-trace read-traces) o))
                               opand-addrs)))
           (scheme->venture (scheme-apply sim arguments))))))

  converts a normal Scheme procedure (e.g. +) to a Venture procedure,
  and:

    (define (scheme-procedure-over-addresses->v1-foreign sim)
      (make-foreign
       (lambda (oper opand-addrs addr cur-trace read-traces)
         (scheme->venture (scheme-apply sim opand-addrs)))))

  allows writing requesters that pass addresses in their requests.

    - The latter also theoretically allows writing procedures like
      selectors that are parametrically polymorphic in their outputs.
      That might be useful for clearer and/or more efficient
      passing-around of objects.

    - TODO: The address version is currently written to require
      returning a value or request object.  Do we want an extension
      allowing it to return an address (with the meaning "return the
      value at that address to my caller")?

- The trampoline is activated by returning a value of a special type.
  To wit, if a procedure application returns an object in the
  "request" type hierarchy, that is interpreted not as a value to pass
  to the caller, but as additional computation to do in the same
  dynamic extent.

    - At minimum, a request specifies a Venture procedure to call,
      arguments wherewith to call it, and a continuation for what to do
      with the result.

        - The continuation is analogous to the OutputPSP, except of course
          it can make a further request; returning a non-request value
          means "return this as my result".

        - Right now, the continuation has to close over the normal
          arguments if it wants to read them; by analogy with v0.2, we
          could tweak the interpreter to pass the original arguments
          to it separately (this should be especially helpful for
          value-reading outputters associated with address-only
          requesters).

    - We also provide a request subtype that supplies
      expression-environment pairs for evaluation.

    - TODO We could also provide a request subtype that solicits the
      evaluation of multiple requests and denotes their conditional
      independence from each other; there would be one shared
      continuation that receives the list of all answers.

- Open question: what's with mem?  Does the support for that need to
  be built in to the trampoline the way it is in v0.2, or can it be
  separated?

    - Decision: defer figuring it out until exchangeable coupling makes
      sense
