from venture.test.config import get_ripl

def testInferLoopSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  
  # Before starting continuous inference, sampling the same variable
  # always gives the same answer.
  v = ripl.sample("x")
  assert v == ripl.sample("x")

  try:
    ripl.infer("(loop ((mh default one 1)))")
    # If continuous inference is really running, the value of x should
    # change without me doing anything
    v = ripl.sample("x")
    assert not v == ripl.sample("x")
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around
