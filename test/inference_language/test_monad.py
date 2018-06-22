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

from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import get_ripl
from venture.test.config import needs_backend
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownContinuous
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest
import venture.ripl.utils as u

@on_inf_prim("none")
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
  # Same as above, but in venture script
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.set_mode("venture_script")
  ripl.execute_program("""
define foo = proc() {
  do(x <- sample(flip()),
     if (x) {
       assume y = true
     } else {
       assume y = false
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
def testModelSwitchingSmoke(seed):
  ripl = get_ripl(seed=seed, persistent_inference_trace=True)
  ripl.execute_program("""
[define normal_through_model
  (lambda (mu sigma)
    (do (m <- (new_model))
        (res <- (in_model m
          (do (assume x (normal 0 ,(* (sqrt 2) sigma)))
              (assume y (normal x ,(* (sqrt 2) sigma)))
              (observe y (* 2 mu))
              (resimulation_mh default one %s)
              (sample x))))
        (return (first res))))]
  """ % default_num_transitions_per_sample())
  predictions = [ripl.infer("(normal_through_model 0 1)") for _ in range(default_num_samples())]
  return reportKnownGaussian(0.0, 1.0, predictions)

@on_inf_prim("in_model")
def testPerModelLabelNamespaceSmoke():
  ripl = get_ripl()
  ripl.execute_program("""
(do (observe (normal 0 1) 3 foo)
    (in_model (run (new_model))
      (do (observe (gamma 1 1) 2 foo))))
""")

@on_inf_prim("in_model")
def testPerModelLabelNamespaceForget():
  ripl = get_ripl()
  ripl.execute_program("""
(do (observe (normal 0 1) 3 foo)
    (m <- (new_model))
    (in_model m
      (observe (gamma 1 1) 2 foo))
    (forget 'foo)
    (in_model m
      (forget 'foo)))
""")

@on_inf_prim("in_model")
def testPerModelLabelNamespaceForgetVS():
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("""
{ foo: observe normal(0, 1) = 3;
  m <- new_model();
  in_model(m, { foo: observe gamma(1, 1) = 2; });
  forget(quote(foo));
  in_model(m, forget(quote(foo)))
}
""")

@on_inf_prim("in_model")
def testPerModelLabelNamespaceForgetAssume():
  ripl = get_ripl()
  ripl.execute_program("""
(do (assume foo (normal 0 1))
    (m <- (new_model))
    (in_model m
      (assume foo (gamma 1 1)))
    (forget 'foo)
    (in_model m
      (forget 'foo)))
""")

@on_inf_prim("in_model")
def testPerModelLabelNamespaceForgetAssume2():
  # The example Marco provided for Issue #540
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("""
define env = run(new_model());

infer in_model(env, {
    assume foo = normal(0, 1);
    foo_obs: observe foo = 1.123;
    assume bar = normal(0, 1);
    bar_obs: observe bar = 4.24;
});

infer in_model(env, do(
    forget(quote(bar_obs)),
    forget(quote(bar)),
    forget(quote(foo_obs)),
    forget(quote(foo))));
""")

@on_inf_prim("return")
@on_inf_prim("action")
def testReturnAndAction():
  eq_(3.0, get_ripl().infer("(do (return 3))"))
  eq_(3.0, get_ripl().infer("(do (action 3))"))

@on_inf_prim("action")
def testLazyAction():
  assert get_ripl().infer("""\
(let ((act (action (normal 0 1))))
  (do (r1 <- act)
      (r2 <- act)
      (return (not (= r1 r2)))))
""")

@on_inf_prim("return")
def testEagerReturn():
  assert get_ripl().infer("""\
(let ((act (return (normal 0 1))))
  (do (r1 <- act)
      (r2 <- act)
      (return (= r1 r2))))
""")

@on_inf_prim("none")
def testDoLet():
  assert get_ripl().evaluate("""\
(do (let x 1)
    (let y x)
    (= x y))
""")

@on_inf_prim("none")
def testDoLetrec():
  assert get_ripl().evaluate("""\
(do (letrec x (lambda () (y)))
    (mutrec y (lambda () 1))
    (= (x) (y)))
""")

@on_inf_prim("none")
def testDoLetValues():
  assert get_ripl().evaluate("""\
(do (let_values (x y) (values_list 1 2))
    (= 3 (+ x y)))
""")

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
      (resimulation_mh default one 5))]

[infer
  (do (m1 <- (new_model 'lite))
      (m2 <- (new_model 'puma))
      (in_model m1 something)
      (in_model m2 something))]
""")

@on_inf_prim("fork_model")
@statisticalTest
def testModelForkingSmoke(seed):
  ripl = get_ripl(seed=seed, persistent_inference_trace=True)
  ripl.execute_program("""
[assume p (beta 1 1)]

[define beta_through_model
  (lambda (a b)
    (do (m <- (fork_model))
        (res <- (in_model m
          (do (repeat (- a 1) (observe (flip p) true))
              (repeat (- b 1) (observe (flip p) false))
              (resimulation_mh default one %s)
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
  (do (resimulation_mh default one 5)
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

@on_inf_prim("report")
def testReportActionSmoke():
  vals = get_ripl().execute_program("""\
foo : [assume x (+ 1 2)]
(report 'foo)
""")
  eq_([3.0, 3.0], u.strip_types([v['value'] for v in vals]))

@on_inf_prim("report")
def testReportObserveActionSmoke():
  vals = get_ripl().execute_program("""\
foo : [observe (normal 0 1) 0.2]
(report 'foo)
""")
  eq_(0.2, u.strip_types(vals[1]['value']))

@on_inf_prim("report")
def testReportObserveListActionSmoke():
  vals = get_ripl().execute_program("""\
[assume m (array 0. 0.)]
[assume s (matrix (array (array 1. 0.) (array 0. 1.)))]
foo : [observe (multivariate_normal m s) (array 0.1 -0.1)]
(report 'foo)
""")
  eq_([0.1, -0.1], u.strip_types(vals[3]['value']))

@on_inf_prim("report")
def testReportObserveInferActionSmoke():
  vals = get_ripl().execute_program("""\
[assume x (normal 0 1)]
foo : [observe (normal x 1) 0.2]
[infer (resimulation_mh default one 1)]
(report 'foo)
""")
  eq_(0.2, u.strip_types(vals[3]['value']))

@on_inf_prim("report")
def testReportObserveListInferActionSmoke():
  vals = get_ripl().execute_program("""\
[assume m (array 0. 0.)]
[assume s (matrix (array (array 1. 0.) (array 0. 1.)))]
foo : [observe (multivariate_normal m s) (array 0.1 -0.1)]
[infer (resimulation_mh default one 1)]
(report 'foo)
""")
  eq_([0.1, -0.1], u.strip_types(vals[4]['value']))

@on_inf_prim("force")
def testForceSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  vals = r.execute_program("""\
assume x = normal(0,1);
force x = 5;
report(quote(x));
""")
  eq_(5, u.strip_types([v['value'] for v in vals])[2])

@on_inf_prim("sample")
def testSampleSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  vals = r.execute_program("sample 2 + 2;")
  eq_([4], u.strip_types([v['value'] for v in vals]))

@on_inf_prim("mh")
def testInferenceWorkCounting():
  r = get_ripl()
  eq_([0], r.infer("(resimulation_mh default one 1)"))
  r.assume("x", "(normal 0 1)")
  eq_([1], r.infer("(resimulation_mh default one 1)"))
  r.observe("(normal x 1)", 2)
  eq_([2], r.infer("(resimulation_mh default one 1)"))

def testLetrecSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  eq_(True, r.evaluate(""" {
      letrec even = (n) -> { if (n == 0) { true  } else {  odd(n - 1) } };
         and odd  = (n) -> { if (n == 0) { false } else { even(n - 1) } };
      odd(5) }
"""))

def testRandomSugar():
  r = get_ripl()
  r.set_mode("venture_script")
  r.infer("""
    { assume x = normal(0, 1);
      frob: observe normal(x, 1) = 5;
      default_markov_chain(10);
      y <- sample x;
      let (y1, y2) = list(ref(y), ref(y));
      return(y1 + y2) }""")

def testTilde():
  r = get_ripl()
  r.set_mode("venture_script")
  r.infer("""
    { assume my_g = (mu) ~> { normal(mu, 1) };
      assume x ~ my_g(0);
      default_markov_chain(10);
      y <~ sample my_g(x);
      return(y)
    }""")

def testInventName():
  r = get_ripl()
  r.set_mode("venture_script")
  r.infer("""
    { name = quote(foo);
      assume $name ~ normal(0, 1);
      sample foo;
    }""")

def testInventLabel():
  r = get_ripl()
  r.set_mode("venture_script")
  r.infer("""
    { label = quote(foo);
      $label : assume bar ~ normal(0, 1);
      sample bar;
    }""")
  r.report('foo')

def testInventLabel2():
  r = get_ripl()
  r.set_mode("venture_script")
  r.infer("""
    { label = quote(foo);
      val <- $label : assume bar ~ normal(0, 1);
      return(val);
    }""")
  r.report('foo')

def testForgettingAcrossModels():
  r = get_ripl()
  r.set_mode("venture_script")
  r.execute_program("""
define env = run(new_model());
infer in_model(env, { assume mu = normal(0, 1); });
define env2 = first(run(in_model(env, fork_model())));
infer in_model(env, forget(quote(mu)));
infer in_model(env2, forget(quote(mu)));
""")
