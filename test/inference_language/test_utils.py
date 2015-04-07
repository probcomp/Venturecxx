from nose.tools import raises, eq_

from venture.test.config import get_ripl, on_inf_prim
import venture.test.errors as err

@on_inf_prim("assert")
def testAssertSmoke():
  get_ripl().infer("(assert true)")

@on_inf_prim("assert")
def testAssertSmoke2():
  err.assert_error_message_contains("""\
((assert false) model)
^^^^^^^^^^^^^^^^^^^^^^
""", get_ripl().infer, "(assert false)")

@on_inf_prim("particle_log_weights")
def testWeightsSmoke():
  get_ripl().infer("(do (w <- particle_log_weights) (assert (eq 0 (lookup w 0))))")

@on_inf_prim("set_particle_log_weights")
def testWeightsSmoke2():
  get_ripl().infer("""(do
  (set_particle_log_weights (array -1))
  (w <- particle_log_weights)
  (assert (eq -1 (lookup w 0))))""")

@on_inf_prim("likelihood_at")
def testLikelihoodSmoke():
  get_ripl().infer("""(do
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (likelihood_at default all))
  (assert (< (lookup l 0) 0)))""")

@on_inf_prim("posterior_at")
def testPosteriorSmoke():
  get_ripl().infer("""(do
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (likelihood_at default all))
  (p <- (posterior_at default all))
  (assert (< (lookup p 0) (lookup l 0))))""")

# TODO Also want statistical test cases for likelihood_at and posterior_at

@on_inf_prim("quasiquote")
def testExplicitQuasiquotation():
  eq_(3, get_ripl().infer("(lambda (t) (pair (lookup (quasiquote ((unquote (+ 1 2)) 5)) 0) t))"))

@on_inf_prim("quasiquote")
def testExplicitQuasiquotation2():
  eq_(3, get_ripl().infer("(lambda (t) (pair (lookup `(,(+ 1 2) 5) 0) t))"))
