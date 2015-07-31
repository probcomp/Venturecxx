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
import time

from venture.test.config import get_ripl, broken_in, on_inf_prim
import venture.test.errors as err
import venture.value.dicts as v


@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testBasicAnnotation():
  sivm = get_ripl().sivm
  expr = v.app(v.sym("add"), v.num(1), v.sym("foo"))
  err.assert_sivm_annotation_succeeds(sivm.assume, v.sym("x"), expr)

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testBasicAnnotation2():
  ripl = get_ripl()
  err.assert_error_message_contains("""\
(add 1 foo)
       ^^^
""",
  ripl.assume, "x", "(+ 1 foo)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateErrorTriggeredByInference():
  ripl = get_ripl()
  ripl.assume("control", "(flip)")
  ripl.force("control", True)
  ripl.predict("(if control 1 badness)")
  err.assert_error_message_contains("""\
(if control 1 badness)
^^^^^^^^^^^^^^^^^^^^^^
(if control 1 badness)
              ^^^^^^^
""",
  ripl.infer, "(mh default one 50)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateProgrammaticAssume():
  ripl = get_ripl()
  err.assert_error_message_contains("""\
(run (assume x (add 1 foo)))
     ^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")
  err.assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateErrorTriggeredByInferenceOverProgrammaticAssume():
  # Do not use the do macro yet
  ripl = get_ripl()
  ripl.infer("(assume control (flip))")
  ripl.infer("(force control true)")
  ripl.infer("(predict (if control 1 badness))")
  # TODO Solve the double macroexpansion problem
  err.assert_error_message_contains("""\
((biplex control (make_csp (quote ()) (quote 1.0)) (make_csp (quote ()) (quote badness))))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
((biplex control (make_csp (quote ()) (quote 1.0)) (make_csp (quote ()) (quote badness))))
                                                                               ^^^^^^^
""",
  ripl.infer, "(mh default one 50)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateDefinedProgrammaticAssume():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", "(lambda () (assume x (+ 1 foo)))")
  # Hm.  Blaming makers of inference actions rather than the actions
  # themselves produces this; which does point to the culprit.
  # However, the top stack frame is somewhat misleading as to when the
  # problem was identified.  I might be able to live with that.
  err.assert_error_message_contains("""\
(run (action))
     ^^^^^^^^
(lambda () (assume x (add 1 foo)))
           ^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(action)")
  err.assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(action)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceProgramError():
  ripl = get_ripl()
  err.assert_error_message_contains("""\
(run (observe (normal 0 1) (add 1 foo)))
                                  ^^^
""",
  ripl.infer, "(observe (normal 0 1) (+ 1 foo))")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceProgramErrorInDefinition():
  ripl = get_ripl(persistent_inference_trace=True)
  err.assert_error_message_contains("""\
(observe (normal 0 1) (add 1 foo))
                             ^^^
""",
  ripl.define, "badness", "(observe (normal 0 1) (+ 1 foo))")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateDefinedInferenceProgramError():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("badness", "(lambda () (observe (normal 0 1) (+ 1 foo)))")
  err.assert_error_message_contains("""\
(run (badness))
     ^^^^^^^^^
(lambda () (observe (normal 0 1) (add 1 foo)))
                                        ^^^
""",
  ripl.infer, "(badness)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateDefinedQuasiquotedProgrammaticAssume():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", "(lambda (name) (assume x (+ 1 ,name)))")
  # Hm.  Blaming makers of inference actions rather than the actions
  # themselves produces this; which does point to the culprit.
  # However, the top stack frame is somewhat misleading as to when the
  # problem was identified.  I might be able to live with that.
  err.assert_error_message_contains("""\
(run (action (quote foo)))
     ^^^^^^^^^^^^^^^^^^^^
(lambda (name) (assume x (add 1 (unquote name))))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(action 'foo)")
  err.assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(action 'foo)")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAssignedDidUniqueness():
  ripl = get_ripl(persistent_inference_trace=True)
  for i in range(20):
    ripl.define("foo%d" % i, "(predict (normal 0 1))")
    ripl.infer("foo%d" % i)
  # Or maybe 60 if I start recording the infer statements too.
  eq_(40, len(ripl.sivm.syntax_dict.items()))

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceErrorInDo():
  # TODO I need the inference trace to be persistent to trigger the
  # inference prelude did skipping hack :(
  ripl = get_ripl(persistent_inference_trace=True)
  expression = """\
(do (assume x (normal 0 1))
    (observe x (+ 1 badness)))"""
  err.assert_error_message_contains("""\
(run (do (assume x (normal 0 1)) (observe x (add 1 badness))))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(run (do (assume x (normal 0 1)) (observe x (add 1 badness))))
                                                   ^^^^^^^
""",
  ripl.infer, expression)

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceErrorInDefinedDo():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", """\
(do (assume x (normal 0 1))
    (y <- (sample x))
    (observe x (+ 1 badness)))""")
  err.assert_error_message_contains("""\
(run action)
^^^^^^^^^^^^
(do (assume x (normal 0 1)) (y <- (sample x)) (observe x (add 1 badness)))
                                                                ^^^^^^^
""",
  ripl.infer, "action")

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceErrorInQuasiquote():
  ripl = get_ripl()
  expression = """\
(inference_action (lambda (t) (pair (lookup `(,(+ 1 badness) 5) 0) t)))
"""
  err.assert_error_message_contains("""\
(run (inference_action (lambda (t) (pair (lookup (quasiquote ((unquote (add 1 badness)) 5)) 0) t))))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(run (inference_action (lambda (t) (pair (lookup (quasiquote ((unquote (add 1 badness)) 5)) 0) t))))
                                                                              ^^^^^^^
""",
  ripl.infer, expression)

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateInferenceErrorInImplicitQuasiquote():
  ripl = get_ripl()
  expression = """\
(assume x (normal ,(+ 1 badness) 1))
"""
  err.assert_error_message_contains("""\
(run (assume x (normal (unquote (add 1 badness)) 1)))
                                       ^^^^^^^
""",
  ripl.infer, expression)

@on_inf_prim("none")
def testLoopErrorAnnotationSmoke():
  import threading
  numthreads = threading.active_count()

  ripl = get_ripl()
  expression = "(loop (inference_action (lambda (t) (pair (+ 1 badness) t))))"
  def doit():
    ripl.infer(expression)
    time.sleep(0.01) # Give it time to start
    ripl.stop_continuous_inference() # Join the other thread to make sure it errored
  err.assert_print_output_contains("""\
(run (inference_action (make_csp (quote (t)) (quote (pair (add 1 badness) t)))))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(run (inference_action (make_csp (quote (t)) (quote (pair (add 1 badness) t)))))
                                                                 ^^^^^^^
""", doit)
  eq_(numthreads, threading.active_count()) # Erroring out in loop does not leak active threads

@broken_in("puma", "Puma does not report error addresses")
@on_inf_prim("none")
def testAnnotateErrorInMemmedProcedure():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda () (normal (+ 1 badness) 1)))")
  err.assert_error_message_contains("""\
(f)
^^^
(mem (lambda () (normal (add 1 badness) 1)))
                               ^^^^^^^
""",
  ripl.predict, "(f)")

@broken_in("puma", "Puma does not report polite exceptions")
def testAnnotationSuppressionSmoke():
  from nose.tools import assert_raises
  from venture.exception import VentureException

  ripl = get_ripl()
  ripl.disable_error_annotation()
  with assert_raises(VentureException) as cm:
    ripl.predict("(f)")
  # I want annotation not to succeed
  assert "stack_trace" not in cm.exception.data

def testAnnotateErrorInEvaluate():
  ripl = get_ripl()
  err.assert_error_message_contains("""\
(autorun (badness))
          ^^^^^^^
""",
  ripl.evaluate, "(badness)")
