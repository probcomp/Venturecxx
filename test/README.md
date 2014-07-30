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

- `regressions/` is the bucket of regression tests.

- `stack/` is tests of the stack (which are predominantly unit tests).

- `unit/` is unit tests of separable pieces (there are quite few of
  these right now).

Configurations
--------------

Many of Venture's test cases naturally apply to both backends, and/or
to a variety of generic inference strategies.  Therefore, the test
runner is configurable, to select which backend to test and which
inference program to use.

When writing tests, we recommend interacting with Venture through the
`venture.test.config` module (in `test/config.py`) to be as generic as
is appropriate for the test.  In particular, if a new test is not
generic across backends, please decorate it with
`@venture.test.config.in_backend` (or `@gen_in_backend` for
generators), whose docstrings see.

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
framework currently live in `test/conformance/sps/test_properties.py`,
and check things like "This SP accepts VentureValues of the types it
is annotated with and returns VentureValues of the types it is
annotated with", or "This type-annotated SP is as deterministic as it
claims to be".
