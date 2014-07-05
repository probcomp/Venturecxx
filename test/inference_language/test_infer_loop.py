from venture.test.config import get_ripl

def testStopSmoke():
  get_ripl().stop_continuous_inference()

def assertInferring(ripl):
  # If continuous inference is really running, the value of x should
  # change without me doing anything
  v = ripl.sample("x")
  assert not v == ripl.sample("x")

def assertNotInferring(ripl):
  # If not running continuous inference, sampling the same variable
  # always gives the same answer.
  v = ripl.sample("x")
  assert v == ripl.sample("x")

def testInferLoopSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)

  try:
    ripl.infer("(loop ((mh default one 1)))")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

def testStartStopInferLoop():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  assertNotInferring(ripl)
  try:
    ripl.infer("(loop ((mh default one 1)))")
    assertInferring(ripl)
    with ripl.sivm._pause_continuous_inference():
      assertNotInferring(ripl)
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around
