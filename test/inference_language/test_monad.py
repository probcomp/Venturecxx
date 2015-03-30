import scipy.stats as stats

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, on_inf_prim, default_num_samples, default_num_transitions_per_sample

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

@on_inf_prim("in_model")
@statisticalTest
def testModelSwitchingSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[define normal_through_model
  (lambda (mu sigma)
    (do (m <- (new_model))
        (res <- (in_model m
          (do (assume x (normal 0 ,(* (sqrt 2) sigma)))
              (assume y (normal x ,(* (sqrt 2) sigma)))
              (observe y (* 2 mu))
              (mh default one %s)
              (sample x))))
        (return (first res))))]
  """ % default_num_transitions_per_sample())
  predictions = [ripl.infer("(normal_through_model 0 1)") for _ in range(default_num_samples())]
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")
