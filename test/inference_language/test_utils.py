from nose.tools import raises

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("assert")
def testAssertSmoke():
  get_ripl().infer("(assert true)")

@on_inf_prim("assert")
@raises(AssertionError)
def testAssertSmoke2():
  get_ripl().infer("(assert false)")

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
