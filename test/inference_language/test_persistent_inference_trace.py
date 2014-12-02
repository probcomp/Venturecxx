from nose.tools import eq_

from venture.test.config import get_ripl

def testPersistenceSmoke1():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[define foo 5]
[assume x (flip 0.1)]
[infer (mh default one foo)]""")

def testPersistenceSmoke2():
  r = get_ripl(persistent_inference_trace=True)
  r.set_mode("venture_script")
  r.execute_program("""
define foo = 5
assume x = flip(0.1)
infer mh(default, one, foo)""")

def testPersistenceSmoke3():
  r = get_ripl(persistent_inference_trace=True)
  r.define("foo", "5")
  r.assume("x", "(flip 0.1)")
  r.infer("(mh default one foo)")

def testInferObserveSmoke1():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume x (normal 0 1)]
[infer (observe x (+ 1 2))]
[infer (incorporate)]""")
  eq_(3, r.sample("x"))

def testInferObserveSmoke2():
  r = get_ripl()
  r.infer("(observe (normal 0 1) 3)")
  r.infer("(incorporate)")
  eq_(3, r.report(1))

def testInlineSMCSmoke():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[define go
  (lambda (ct)
    (if (< ct 20)
        (begin
          (observe (normal 0 1) ct)
          (resample 1)
          (go (+ ct 1)))
        pass))]

[infer (go 0)]
[infer (incorporate)]
""")
  for i in range(20):
    eq_(i, r.report(i+1))

def testInlineSMCSmoke2():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume frob (mem (lambda (i) (uniform_continuous -100 100)))]
[define go
  (lambda (ct)
    (if (< ct 20)
        (begin
          (observe (frob (unquote ct)) ct)
          (resample 1)
          (go (+ ct 1)))
        pass))]

[infer (go 0)]
[infer (incorporate)]
""")
  for i in range(20):
    eq_(i, r.sample("(frob %s)" % i))

def testDirectivesInInfer1():
  r = get_ripl()
  r.infer("(assume x 5)")
  eq_(5, r.sample("x"))

def testDirectivesInInfer2():
  r = get_ripl()
  r.infer("(predict (+ 5 2))")
  eq_(7.0, r.report(1))
