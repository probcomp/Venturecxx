Notes on Venture error reporting
================================

Alexey Radul, 3/17/15

I am stopping work on error reporting for now, becuase it got better
and I am tired of wrangling with it.  I am recording my notes here in
hopes that they may help the next person (likely me again later) to
regain context.

Overview
--------

Error reporting is a pain because errors are generally detected when
operating on some machine-oriented representation, but in order to be
useful need to be reported in terms of the source representation the
programmer actually wrote.

In Venture as it stands now, there are actually two notions of "where
did an error happen":

- The point in the inference program that triggered the error.

- The point in the model program that was being regenerated at the
  time, if any.

There are also three representations for the location of an error:

- Address in the (model or inference) trace.

- Stack of structured pointers into structured expressions.

- Stack of indexes into strings.

The current (somewhat baroque) error management architecture is this:

1. The outermost layer (ripl) parses string source expressions into
   list and dict structured expressions.

       - Any parse errors are reported by source location in the
         string fragment being parsed, which may be slightly wierd if
         the expression came in through the API.

       - After a successful parse, the mapping between the original
         text position and the structured parse result is lost.

2. The next layer (sivm) expands macros, and stores a table mapping
   directive ids to the information it needs to invert macro expansion
   for error reporting.

       - The information in question is a) the original expression,
         and b) the Syntax object returned by the macro expander.  The
         Syntax knows how to transform structured pointers to and from
         the macroexpanded form, but may not in general be able to
         reconstruct the original expression.  See
         [../python/lib/sivm/macro_system.py] and
         [../python/lib/sivm/pattern_language.py].

       - Complication: directive ids are actually assigned by the
         Engine, so the sivm maintains a stack of macro expansions of
         directives currently in progress.

3. The next layer (engine) actually executes the desired computation
   in either the inference or the model trace.

4. Most error conditions are detected in regen, as missing symbols or
   inappropriate SP applications.

   - If an SP or a symbol lookup raises an exception which is a
     subclass of `VentureError` (currently), regen will catch it,
     annotate it with the trace address of the faulty node, and
     re-raise it as a `VentureException`.

5. In the event of an error, the sivm:

   - Catches `VentureException`s,
   - Reads their trace addresses,
   - Annotates them with stack traces which are computed from the
     trace address and the stored table of macro expansion results
     (the first element of the address is the directive id where the
     error occurred, etc), and
   - Reraises them.

6. In the event of an error, the ripl:

   - Catches `VentureException`s,
   - Reads their stack trace annotations,
   - Unparses those expressions,
   - Translates the structured expression indexes into textual indexes
     on the strings (this apparently requires re-parsing the
     expression),
   - Annotates the exception with the above information in
     table-of-strings form, and
   - Re-raises them.

7. The `__str__` method of `VentureException` looks for the above
   annotations and tries to render them in a reasonably human-readable
   way.

Important caveat to all the above: The sivm and the ripl are both
reentrant, because some inference SPs reach up the stack and call ripl
methods to add assumes, observes, etc. to the model.  Such SPs catch
`VentureException`s that come out of the ripl method they call, and
wrap them in `VentureError`s, so that they may go through the whole
error reporting pipeline again and acquire an inference-level error
description as well as the model-level one.

Further Facts
-------------

- There's all this nonsesnse involving a non-existent debugger and
  states system cluttering up the venture sivm code.

- It seems that the sivm annotator never sees breakpoint or parse
  exceptions in the test suite.  (Or the innermost variety of invalid
  argument exception, but that seems less important.)

- The macro expander raises "parse" exceptions!?

- Stack dict -> venture value -> stack dict is not the identity
  function, and can't be because it collapses [stack dict] and
  v.array([stack dict]) into the same representation.

- Do I want string -> stack dict -> string by unparse . parse to be
  the identity function (up to white space, comments?)?

    - Currently, I expect it is not, because I expect it will
      canonicalize array<[json stuff]> to (stuff)

- I'm pretty sure that venture value -> stack dict -> venture value
  is the identity.

    - Except horrible Venture values like (compound) SPs

    - There is even a test of this

- Do I want stack dict -> string -> stack dict by parse . unparse to be
  the identity function?

    - It's possible that it is.

    - The version restricted to stack dicts that come out of polite
      venture values is checked for identity by a test.

- Do I want string -> stack dict -> venture value -> stack dict -> string
  by unparse . toStackDict . fromStackDict . parse to be the identity?

    - It can't because it has to canonicalize arrays one way or the other

    - It also canonicalizes number literals to floats

- Q: Is there any reason not to just delete the debugger instructions?
  They are unexercised, and I have likely to broken them further.

Explanations
------------

- Venture sivm error annotation code was written assuming there is
  just one model trace, and there is a mapping between directive ids
  and model trace elements, and that all exceptions are a result of an
  exception in regen in the model trace.

    - No facility for blaming parts of the inference program

    - No facility for blaming failures internal to the inference program

    - Original expectation was that inference programming would operate on
      a whole sivm/ripl, so would use the annotation machinery attached to
      its model for in-model exceptions.

        - Then, if the inference program itself was in a ripl, there would
          be nested annotations.

    - The current state of affairs is a twist on that original
      intention, reusing the sivm machinery by noting that the code is
      actually agnostic as to what trace the expressions it annotates
      were evaluated in.

        - In order for this to work, the engine now assigns globally
          unique directive ids.

- Q: What are addresses and indexes?
  A:

    - An Address is effectively a (backwards) linked list of stack
      frames, where each stack frame amounts to a (desugared) source
      location.  The location is represented as (linked) list of
      integers.  The first is the directive id, and the rest is a
      rose-tree index: each integer indexes into the corresponding
      array of (sub)expressions.

    - Regen builds addresses and stores them in the nodes

    - There may be problems with things like mem (which construct
      expressions to be evaluated that have no source locations)

        - There is some hack for making the message look good

- Q: Why does the ripl _overwrite_ the stack trace field of the
  exception it's annotating?  That impedes debugging it.
  A: No good reason.

Outstanding Problems
--------------------

- [double macroexpansion] Directives that are made programmatically
  will be macroexpanded due to their participation in the inference
  trace, and so will register in the model-related directive map in
  their expanded form.  I expect this to produce rather ugly
  annotations (but, at least in the inference program error comments
  it should be fine).

    - One approach: suppress macroexpansion inside quoted stuff Does
      my quasiquote implementation already do that?

- Puma doesn't report error addresses at all.

- "Real" inference sps like mh do not trap and wrap regen exceptions
  the way the ripl-passing ones do.  Also, even if they did, then
  error annotation code does not try to annotate cause exceptions
  (though perhaps it should).

- SLAM is losing because the form is not pretty-printed, and is much
  too long to fit on one line for the underlining to work.

Approaches to the double-macroexpansion problem
-----------------------------------------------

- Could define "quote" to be "data-quote".  If so:

    - the macro expander needs to be aware of quote and quasiquote and
      not recur inside

    - eval needs to call macro expansion

    - disasters like make_csp either need to call macro expansion or
      need to vanish and be replaced by lambda being a proper special
      form

        - calling macroexpansion is currently complicated because the
          inverse needs to be stored for error reporting, and currently
          the sivm is trying to be in charge of that.

        - Could hack this partially by having the macroexpander recur into
          lambda bodies in spite of them expanding into make_csp of quote,
          which leaves user-constructed calls to make_csp in a lurch.

- Alternately, could define "quote" to be "syntax-quote".  If so, it's
  perfectly reasonable for the object returned by a syntax-quote to be
  some elaborate syntax object that has already been macro-expanded,
  and knows how to macro-collapse itself.

    - Could also augment eval to normalize lists into syntax objects
      with missing meta-data (and possibly re-macroexpand them).


Anticipated Future Problems
---------------------------

- In errors that happen during actual inference, I expect to lose the
  information of where in the inference program a given programmatic
  directive was added to the model.  Perhaps I do not need it.

- The macro expander recurs into array literals.  This means there is
  currently no way to suppress macroexpansion (quote doesn't).

- Should verify that an assume-forget loop in an inference program
  does not accumulate state in the ripl or sivm.

- The sivm never sees the inference or model prelude definitions, so
  is likely to mess up on stack traces that go through calls to those
  functions.  [There is a hack for this in place wrt the inference
  prelude.]

- The sivm is likely to leak sugar_dict entries in non-persistent
  inference trace mode, if I start recording desugarings of infer
  instructions.

- The currently executing expression is not the only one the sivm
  doesn't have in its sugar dict: there are also the inference and
  model preludes.  This may causes confusion.

    - I may have hacked the inference prelude problem satisfactorily,
      but maybe not.

- [hacked] [blaming makers] Crashing in a programmatic assume by
  default blames the application of the made action SP, even though
  the mistake is made in the application of the maker.  If it were a
  normal compound, the evaluator would recur into the body, and so
  blame the body form; but as it is, it blames the application of the
  made primitive, which is uninformative.  Perhaps this is a general
  phenomenon with higher-order primitive procedures.

    - Intervention: Permit SPs that throw exceptions to indicate extra
      pieces of address to be included in the error report, which their
      maker can presumably extract from the args struct.

    - Second intervention: Blame the call to the maker rather than the
      (mythical) body of the made procedure, by replacing the error
      address in the `VentureException` thrown by regen.  This is not
      actually analogous to compound procedures.

- Do the syntax rules style macros emit raw symbols from the template
  (as opposed to stack-dict-wrapped symbols) into the result
  expressions?  Is that going to ever be a problem?

Milestones
----------

(+ means "done", - means "to do")

+ A bad assume directive gives an accurate error
- An infer that triggers badness in an assume gives an accurate error
  + to the model program
  - to the inference program
+ A bad assume inference action gives an accurate error to the model
  and the inference program
- An infer that triggers badness in an assume made by an action gives
  an accurate error
  + to the model program (if macroexpanded)
  - to the model program without spurious macro expansion
  - to the inference program
+ A bad assume inside a define gives an accurate error
  + to the model program
  + to the inference action in the define
- Same for infer action over such
+ A bad inference expression (that fails without interacting with the
  model) gives an accurate error
+ Same if it occurs in a define
+ Same if it occurs in a do block
+ Same if it occurs in a do block in a define
+ Same if it occurs in a quasiquotation
+ Same if it occurs in a (quasiquoted) assume form
- A model-bad quasiquoted assume gives an accurate error
  + to the model
  - to the model program without spurious macro expansion
  + to the inference program
- Same for infer action over such
- Can I get a situation where I need a stack trace into a
  later-executed piece of inference code that was introduced in a
  lambda inside of a non-define infer command?  (This should tickle
  recording the macroexpansions of infer directives).
+ Error reporting should not get screwed up even if separately-counted
  did streams would overlap.
- Should get an accurate error even if some stack frames go through the
  model prelude
- Should get an accurate error even if some stack frames go through the
  inference prelude
- All the above in the body of every macro in the book
  - But, may be able to get away with unit testing the index
    resugarers of the macros.
- All the above for venture -f, typing at the console,
  ripl.execute_instruction, and programmatic use (in the case of
  programmatic use, ideally would include the Python trace to the
  point that called the method that triggered the problem).
- Ideally, "accurate error" includes the Python stack into the
  primitive that was being evaluated, in case it's a foreign
  procedure.
  - Actually, for developers, the full Python stack might not be
    unreasonable either (as in "this user program triggered this
    system crash").
- Ideally, Puma would also participate in the error reporting
  protocol.  (My trivial example did not yield the desired stack trace
  when I ran it in Puma)
- It is important to make sure that attempts to annotate or describe
  errors do not mask them if they themselves fail.
- Theoretically, I would test all the above with a generator that made
  errors of many different kinds, but perhaps one will do for
  starters.
- Test that the kinds of errors I was getting in slam actually get
  good messages now.
