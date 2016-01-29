# Copyright (c) 2015, 2016 MIT Probabilistic Computing Project.
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

from nose.tools import eq_

import scipy.stats as stats

from venture.test.stats import statisticalTest, reportKnownGaussian, reportKnownContinuous
from venture.test.config import get_ripl, on_inf_prim, default_num_samples, default_num_transitions_per_sample, needs_backend
import venture.ripl.utils as u

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

@on_inf_prim("assume")
def testMonadicAssume():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[define foo
  (lambda ()
    (do
      (z <- (assume x (flip)))
      (if z
          (assume y true)
          (assume y false))))]
""")
  eq_(ripl.infer("(foo)"), ripl.sample("x"))

@on_inf_prim("predict")
def testMonadicPredict():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[define foo
  (lambda ()
    (do
      (z <- (predict (flip) pid))
      (if z
          (assume y true)
          (assume y false))))]
""")
  eq_(ripl.infer("(foo)"), ripl.report("pid"))

@on_inf_prim("observe")
def testMonadicObserve():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[define foo
  (lambda ()
    (do
      (rho <- (observe (flip) true pid))
      (xi <- (forget 'pid))
      (return (list (mapv exp rho) (mapv exp xi)))))]
""")
  [[rho], [xi]] = ripl.infer("(foo)")
  eq_(rho, xi)
  eq_(rho, 0.5)

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
  return reportKnownGaussian(0.0, 1.0, predictions)

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

@on_inf_prim("fork_model")
@statisticalTest
def testModelForkingSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""
[assume p (beta 1 1)]

[define beta_through_model
  (lambda (a b)
    (do (m <- (fork_model))
        (res <- (in_model m
          (do (repeat (- a 1) (observe (flip p) true))
              (repeat (- b 1) (observe (flip p) false))
              (mh default one %s)
              (sample p))))
        (return (first res))))]
  """ % default_num_transitions_per_sample())
  predictions = [ripl.infer("(beta_through_model 3 2)") for _ in range(default_num_samples())]
  cdf = stats.beta(3,2).cdf
  return reportKnownContinuous(cdf, predictions)

@needs_backend("lite")
@needs_backend("puma")
@on_inf_prim("fork_model")
def testBackendForkingSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.execute_program("""\
[assume x (normal 0 1)]
[observe (normal x 1) 2]

[define something
  (do (mh default one 5)
      (predict (+ x 1)))]

[infer
  (do (m1 <- (fork_model 'lite))
      (m2 <- (fork_model 'puma))
      (in_model m1 something)
      (in_model m2 something))]
""")

@on_inf_prim("autorun")
def testAutorunSmoke():
  eq_(3.0, get_ripl().evaluate("(sample 3)"))

def testReportActionSmoke():
  vals = get_ripl().execute_program("""\
foo : [assume x (+ 1 2)]
(report 'foo)
""")
  eq_([3.0, 3.0], u.strip_types([v['value'] for v in vals]))

def testForceSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  vals = r.execute_program("""\
assume x = normal(0,1);
force x = 5;
report(quote(x));
""")
  eq_(5, u.strip_types([v['value'] for v in vals])[2])

def testSampleSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  vals = r.execute_program("sample 2 + 2;")
  eq_([4], u.strip_types([v['value'] for v in vals]))
