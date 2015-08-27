The Venture test suite
======================

Organization
------------

The test suite lives in the `test/` directory.

- `core/` is small tests of essential pieces of the Venture language
  (modeling, as opposed to inference control).

- `conformance/` is tests of details -- choices that could have gone
  one way or another given the core, pinned down to go the way we
  chose.

- `inference_language/` is tests of features related to inference
  control.

- `inference_quality/micro/` is tiny programs, where we are testing
  discovery (and hopefully ergodic exploration) of the proper posterior.

- `inference_quality/end_to_end/` is bigger programs, that actually
  are or resemble models somebody might use.

- `integration/` is end to end tests that various visible artifacts do
  not crash on invocation.

- `performance/` is testing performance, including asymptotics.

- `properties/` are the randomized tests (see below).

- `regressions/` is the bucket of regression tests.

- `stack/` is tests of the stack (which are predominantly unit tests).

- `unit/` is unit tests of separable pieces (there are quite few of
  these right now).

Crash Testing vs Inference Quality Testing
------------------------------------------

General software has broadly two kinds of correctness failures:
crashes and getting the wrong answer.  When the right answer for a
given test situation is deterministic and sufficiently easily
obtainable, these modes can be conflated by causing an artificial
crash when the answer is wrong -- this is how all the fooUnit testing
frameworks operate.

Venture's notion of a "correct answer" is more subtle, because the
"correct answer" is actually a probability distribution on outputs.
As such, knowing whether the distribution is right or wrong tends to
take a lot of computation, and even then remains uncertain.

Consequently, when testing Venture we separate the notion of checking
for crashes, which always indicate bugs, from the notion of checking
that probabilistic programs written in Venture have the expected
distributional behavior.  The former tends to be relatively fast and
clear-cut (a situation either caused a crash or it didn't), while the
latter consumes much more compute, and is prone to problems that
manifest only sporadically and are difficult to diagnose.

Therefore, axch for one tends not to run the inference quality test
suite much locally, relying instead on the [continuous integration
server](https://probcomp-3.csail.mit.edu/) to
notice problems.  If you are working on something related, however,
`nosetests -c inference-quality.cfg` is your friend.

Note: One can and we do run inference quality tests as crash tests by
taking fewer samples and fewer iterations of any inference method, and
ignoring the statistical properties of the results.  This is turned on
by passing `--tc=ignore_inference_quality:true` to nose, which the
various `crashes.cfg` files do.

Configurations
--------------

Many of Venture's test cases naturally apply to both backends, and/or
to a variety of generic inference strategies.  Therefore, the test
runner is configurable, to select which backend to test and which
inference program to use.

When writing tests, we recommend interacting with Venture through the
`venture.test.config` module (in `test/config.py`) to be as generic as
is appropriate for the test.  In particular:

- if a new test is not generic across backends, please decorate it
  with `@venture.test.config.in_backend` (or `@gen_in_backend` for
  generators), whose docstrings see.

- if a new test is not generic across inference programs, please
  decorate it with `@venture.test.config.on_inf_prim` (or
  `@gen_on_inf_prim` for generators), whose docstrings see.

Statistical Tests
-----------------

Often, a given test situation is expected to produce some distribution
on answers, and should be judged incorrect if it does not.  The
`venture.test.stats` module (in `test/stats.py`) provides some helper
procedures for testing more effectively in these circumstances.

The general pattern: annotate such a test `@statisticalTest`, and have
it `return reportKnownSomething(...)` as appropriate from the helpers
in the `stats` module.

Randomized Tests
----------------

Not to be confused with statistical tests.

The idea of randomized testing is that instead of spelling out
particular examples that should behave in some predicted way, one
spells out properties that should hold true of all inputs, and the
testing framework generates random examples on which to try them.  If
the property fails on even one example, the test fails (this is why
these are different from statistical tests).

Venture has a modest custom randomized testing framework, that only
supports testing properties that are supposed to be true of all
VentureValues (possibly restricted to some type).  The framework
itself is in `test/randomized.py`, with a generator for random
VentureValues in `test/random_values.py`.  The extant tests using the
framework currently live in `test/properties/`,
and check things like "This SP accepts VentureValues of the types it
is annotated with and returns VentureValues of the types it is
annotated with", or "This type-annotated SP is as deterministic as it
claims to be".

Jenkins Continuous Build
------------------------

The continuous build server lives at https://probcomp-3.csail.mit.edu/

The build structure is as follows:

- `venture-crashes` is intended to exercise all the code reasonably
  quickly to check for crashes.  It runs the `all-crashes` script.

- `venture-inference-quality` and the nine other builds named
  `<backend>-<method>-inference-quality` are intended to make sure
  that various probabilistic programs actually sample from the
  distributions we expect, in each backend and exercising each
  inference strategy we have built in.

    - `venture-inference-quality` should really be named
      `lite-mh-inference-quality`.

    - `puma-{meanfield,rejection}-inference-quality` are disabled
      because Puma does not implement those two methods (yet).

    - `lite-{meanfield,func-pgibbs}-inference-quality` are disabled
      because they have never passed.

    - `<backend>-misc-inference-quality` test methods we do not have
      many tests for, as well as combinations of methods.

- `venture-performance` and `puma-performance` confirm a handful of
  asymptotic performance properties on a few examples.

The test selection is done via nose attributes installed by the
`@in_backend` and `@on_inf_prim` decorators.  If you want to grok
how the selection actually happens, read `base.cfg`.
