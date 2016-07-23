Frequently Asked Questions
--------------------------

Q: What is the story with this `unquote`?

If I write::

    (assume x (mem (lambda (i)
      (flip theta_x))))

    [define observer
        (lambda (i xi)
                (observe (x (unquote i)) xi))]

it works, but if I omit the `unquote` I get an error when calling
`(observer 1 True)`, giving `VentureException: *** evaluation: Cannot
find symbol 'i'`

A: This has to do with there being two distinct "contexts" where
expressions may be interpreted: the toplevel (inference) language, and
the model. You can think of these as being totally separate; they
actually have different interpreters.

Normally if you just type an expression in, like `(normal 0 1)`, it
gets evaluated in the inference language. However, so-called "modeling
directives" `assume`, `observe`, etc, operate on the model.

The confusing part is that what actually happens when you do `(observe
(x i) xi)`, is that the expression `(x i)` is automatically quoted --
that is, treated as an expression that is handed to `observe` (which
evaluates it in the model context), rather than evaluated immediately
in the inference context.

Actually, it's _quasi_quoted, which means that, while it is an
expression, you can still get things from the inference language into
it by using `unquote`, which you can think of as expression
interpolation (sort of like string interpolation).

So you have this local variable `i`, which lives in the inference
language, and what you want is to construct an expression `(x ${the
value of i})` and that is the thing whose result you want to
observe. So you use `(unquote i)` to do that.

If you instead just did `(x i)`, that would treat `i` as a variable in the
model, which would only work if that variable was previously defined
in the model (such as by `assume`).

If you like, you can sort of think of it as running this on the
command line::

    python -c "$foo"

versus::

    python -c "foo"

In the first case there is a variable in the outer context that is
being spliced into the expression in the inner language; in the second
case there is just a symbol, which is interpreted as a variable
reference in the inner lnaguage.

Q: Why is the `venture` console ignoring the `--abstract-syntax` flag when
reading a file written in the abstract syntax?

For instance::

    $ cat foo.vnts
    (assume earth_radius 6378)
    $ venture --abstract-syntax -f foo.vnts
    Tracing models with the Lite backend
    Traceback (most recent call last):
    venture.exception.VentureException: *** text_parse: Syntax error at 'earth_radius' (token 2)
    (assume earth_radius 6378)
            ^^^^^^^^^^^^
    {'instruction_string': '(assume earth_radius 6378)', 'text_index': [8, 19]}

A: The extension in `foo.vnts` tells the console to interpret the
program in the concrete syntax, regardless of the `--abstract-syntax` flag. To
ensure the program is interpreted in the abstract syntax, use the extension
`foo.vnt` instead (without the `s`).

Q: What is the difference between `sample` and `predict`?

A: Mnemonic: `sample` is `predict` and `forget`.  To wit, the
`predict` directive evaluates its expression, conditioned on
everything else present in the model, *and records it* in the model.
The `sample` operation, on the other hand, samples the value of its
expression, conditioned on the current state of the model, *and leaves
the model unchanged*.  This causes several differences:

1) Every call to the same `sample` is independent and identically
   distributed (conditioned on the state of the model), whereas
   successive calls to `predict` may influence each other, if
   exchangeably coupled SPs are involved.

2) Repeated `predict` will consume increasing amounts of memory
   tracing the predictions, whereas repeated `sample` will leave
   total memory use unchanged.

3) A `predict` creates a numbered (and optionally labeled) directive,
   which can later be inspected with `report`, `list_directives`, etc.

4) The `predict` ed expression will affect future inference: any
   random choices therein are subject to inference themselves, and may
   act as (soft) contraints on their parent choices.  In the case of
   `default_markov_chain`, an unintentional `predict` may therefore
   increase rejection rates and slow convergence.
