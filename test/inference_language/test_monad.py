# Copyright (c) 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import scipy.stats as stats
from nose.tools import eq_

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, on_inf_prim, default_num_samples, default_num_transitions_per_sample, needs_backend

def testInferenceLanguageEvalSmoke():
  ripl = get_ripl()
  eq_(4,ripl.evaluate(4))
  eq_(4,ripl.evaluate("4"))

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

@on_inf_prim("return")
@on_inf_prim("action")
def testReturnAndAction():
  eq_(3.0, get_ripl().infer("(do (return 3))"))
  eq_(3.0, get_ripl().infer("(do (action 3))"))

@needs_backend("lite")
@needs_backend("puma")
@on_inf_prim("new_model")
def testBackendSwitchingSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""\
[define something
  (do (assume x (normal 0 1))
      (observe (normal x 1) 2)
      (predict (+ x 1))
      (mh default one 5))]

[infer
  (do (m1 <- (new_model 'lite))
      (m2 <- (new_model 'puma))
      (in_model m1 something)
      (in_model m2 something))]
""")

@on_inf_prim("autorun")
def testAutorunSmoke():
  eq_(3.0, get_ripl().evaluate("(sample 3)"))
