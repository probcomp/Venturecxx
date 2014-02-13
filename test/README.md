Organization of the Venture test suite
======================================

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
