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

from nose.tools import eq_

from venture.test.config import broken_in
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
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

@on_inf_prim("equalize_particle_log_weights")
def testWeightsSmoke3():
  get_ripl().infer("""(do
  (resample 2)
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (equalize_particle_log_weights)
  (w <- (particle_log_weights))
  (assert (eq (lookup w 0) (lookup w 1))))""")

@on_inf_prim("log_likelihood_at")
def testLikelihoodSmoke():
  get_ripl().infer("""(do
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (log_likelihood_at default all))
  (assert (< (lookup l 0) 0)))""")

@on_inf_prim("log_likelihood_at")
def testLikelihoodOnNumericBlock():
  get_ripl().infer("""(do
  (assume x (tag 'value 0 (normal 0 1)))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (log_likelihood_at 'value 0))
  (assert (< (lookup l 0) 0)))""")

@on_inf_prim("log_joint_at")
def testPosteriorSmoke():
  get_ripl().infer("""(do
  (assume x (normal 0 1))
  (observe (normal x 1) 2)
  (incorporate)
  (l <- (log_likelihood_at default all))
  (p <- (log_joint_at default all))
  (assert (< (lookup p 0) (lookup l 0))))""")

@on_inf_prim("log_likelihood_at")
def testEmptyScopes():
  get_ripl().infer("""(do
  (assert (eq 0 (lookup (run (log_likelihood_at default one)) 0)))
  (assert (eq 0 (lookup (run (log_joint_at default one)) 0))))""")

# TODO Also want statistical test cases for log_likelihood_at and log_joint_at

@on_inf_prim("quasiquote")
def testExplicitQuasiquotation():
  eq_(3, get_ripl().infer("(inference_action (lambda (t) (pair (lookup (quasiquote ((unquote (+ 1 2)) 5)) 0) t)))"))

@on_inf_prim("quasiquote")
def testExplicitQuasiquotation2():
  eq_(3, get_ripl().infer("(inference_action (lambda (t) (pair (lookup `(,(+ 1 2) 5) 0) t)))"))

@on_inf_prim("value_at")
@broken_in("puma", "Puma does not support select")
def testValueAt():
  eq_(7, get_ripl(init_mode="venture_script").infer("""{
assume x = normal(0, 1) #foo:1;
set_value_at(/?foo==1, 7);
return(value_at(/?foo==1)) }"""))

@on_inf_prim("value_at2")
@broken_in("puma", "Puma does not support select")
def testValueAt2():
  eq_(7, get_ripl().infer("(do (assume x (tag 'foo 1 (normal 0 1))) (set_value_at2 'foo 1 7) (return (value_at2 'foo 1)))"))


def test_resetting_to_prior():
    ripl = get_ripl()
    ripl.set_mode('venture_script')
    ripl.assume('x', 'normal(0, 1)')
    x1 = ripl.sample('x')
    ripl.execute_program('reset_to_prior()')
    x2 = ripl.sample('x')
    assert x1 != x2

