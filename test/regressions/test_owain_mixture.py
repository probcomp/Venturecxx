from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("mh")
def testOwainMixture():
  """Owain got <Exception: Cannot make random choices downstream of a node that gets constrained during regen> and thinks this is a mistake. DHS cannot reproduce the error."""
  ripl = get_ripl()
  ripl.assume("alpha","(uniform_continuous .01 1)")
  ripl.assume("crp","(make_crp alpha)")
  ripl.assume("z","(mem (lambda (i) (crp) ) )")
  ripl.assume("mu","(mem (lambda (z) (normal 0 5) ) )")
  ripl.assume("sig","(mem (lambda (z) (uniform_continuous .1 8) ) )")

  ripl.assume("x","(mem (lambda (i) (normal (mu (z i)) (sig (z i))))  )")

  ripl.assume("w","(lambda (z) 1)")
  ripl.assume("f","(lambda (z x) (* (w z) x) )")

  ripl.assume("y","(mem (lambda (i) (normal (f (z i) (x i)) .1) ) )")

  for i in range(10):
    ripl.observe('(x %i)' %i, '%f' % 1.0)
    ripl.observe('(y %i)' %i, '%f' % 2.0)

  for i in range(10,20):
    ripl.observe('(x %i)'%i,'%f' % 3)
    ripl.infer(10)
    for _ in range(20):
      ripl.predict(["y", i])

  ripl.infer(100)
  
  
  ## without memoizing y's

  ripl = get_ripl()
  ripl.assume("alpha","(uniform_continuous .01 1)")
  ripl.assume("crp","(make_crp alpha)")
  ripl.assume("z","(mem (lambda (i) (crp) ) )")
  ripl.assume("mu","(mem (lambda (z) (normal 0 5) ) )")
  ripl.assume("sig","(mem (lambda (z) (uniform_continuous .1 8) ) )")

  ripl.assume("x","(mem (lambda (i) (normal (mu (z i)) (sig (z i))))  )")

  ripl.assume("w","(lambda (z) 1)")
  ripl.assume("f","(lambda (z x) (* (w z) x) )")

  ripl.assume("y","(lambda (i) (normal (f (z i) (x i)) .1) )")

  for i in range(10):
    ripl.observe('(x %i)' %i, '%f' % 1.0)
    ripl.observe('(y %i)' %i, '%f' % 2.0)

  for i in range(10,20):
    ripl.observe('(x %i)'%i,'%f' % 3)
    ripl.infer(10)
    for _ in range(20):
      ripl.predict(["y", i])

  ripl.infer(100)
