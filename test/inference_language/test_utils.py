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

from nose.tools import raises, eq_

from venture.test.config import get_ripl, on_inf_prim
import venture.test.errors as err

@on_inf_prim("assert")
def testAssertSmoke():
  get_ripl().infer("(assert true)")

@on_inf_prim("assert")
def testAssertSmoke2():
  err.assert_error_message_contains("""\
(run (assert false))
^^^^^^^^^^^^^^^^^^^^
""", get_ripl().infer, "(assert false)")

@on_inf_prim("particle_log_weights")
def testWeightsSmoke():
  get_ripl().infer("(do (w <- (particle_log_weights)) (assert (eq 0 (lookup w 0))))")

@on_inf_prim("set_particle_log_weights")
def testWeightsSmoke2():
  get_ripl().infer("""(do
  (set_particle_log_weights (array -1))
  (w <- (particle_log_weights))
  (assert (eq -1 (lookup w 0))))""")

@on_inf_prim("likelihood_at")
def testLikelihoodSmoke():
  get_ripl().infer("""(do
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (likelihood_at default all))
  (assert (< (lookup l 0) 0)))""")

@on_inf_prim("likelihood_at")
def testLikelihoodOnNumericBlock():
  get_ripl().infer("""(do
  (assume x (tag 'value 0 (normal 0 1)))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (likelihood_at 'value 0))
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
  eq_(3, get_ripl().infer("(inference_action (lambda (t) (pair (lookup (quasiquote ((unquote (+ 1 2)) 5)) 0) t)))"))

@on_inf_prim("quasiquote")
def testExplicitQuasiquotation2():
  eq_(3, get_ripl().infer("(inference_action (lambda (t) (pair (lookup `(,(+ 1 2) 5) 0) t)))"))
