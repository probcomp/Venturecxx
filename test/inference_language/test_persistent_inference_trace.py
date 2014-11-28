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
