





















#### Not sure where this should go
def testForget1():
  ripl = RIPL()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id1")
  ripl.forget("id2")
  ripl.forget("id3")

  real_sivm = ripl.sivm.core_sivm.engine
  assert real_sivm.get_entropy_info()["unconstrained_random_choices"] == 1
  assert real_sivm.logscore() < 0
  return reportPassage("TestForget1")





### These tests are illegal Venture programs, and cause PGibbs to fail because
# when we detach for one slice, a node may think it owns its value, but then
# when we constrain we reclaim it and delete it, so it ends up getting deleted
# twice.

# def testObserveAPredict1(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip 0.0) (lambda () (flip)) (mem (lambda () (flip))))")
#   ripl.predict("(f)")
#   ripl.observe("(f)","true")
#   ripl.predict("(f)")
#   predictions = collectSamples(ripl,2,N)
#   ans = [(True,0.75), (False,0.25)]
#   return reportKnownDiscrete("TestObserveAPredict1", ans, predictions)
















