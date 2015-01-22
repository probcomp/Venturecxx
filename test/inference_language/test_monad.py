from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("sample")
def testMonadicSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[define foo
  (lambda ()
    (do
      (x <- (sample (flip)))
      (if x
          (assume y true)
          (assume y false))))]
""")
  ripl.infer("(foo)")
  assert isinstance(ripl.sample("y"), bool)

@on_inf_prim("sample")
def testMonadicSmoke2():
  """Same as above, but in venture script"""
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.set_mode("venture_script")
  ripl.execute_program("""
define foo = proc() {
  do(x <- sample(flip()),
     if (x) {
       assume(y, true)
     } else {
       assume(y, false)
     })}
""")
  ripl.infer("foo()")
  assert isinstance(ripl.sample("y"), bool)
