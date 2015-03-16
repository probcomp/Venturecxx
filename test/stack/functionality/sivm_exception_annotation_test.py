from nose.tools import assert_raises, eq_

from venture.test.config import get_ripl
from venture.exception import VentureException
import venture.value.dicts as v

def assert_annotation_succeeds(f, *args, **kwargs):
  with assert_raises(VentureException) as cm:
    f(*args, **kwargs)
  assert "stack_trace" in cm.exception.data

def assert_error_message_contains(text, f, *args, **kwargs):
  text = text.strip()
  with assert_raises(VentureException) as cm:
    f(*args, **kwargs)
  message = str(cm.exception)
  if text in message:
    pass # OK
  else:
    print "Did not find pattern"
    print text
    print "in"
    import traceback
    print traceback.format_exc()
    print cm.exception
    assert text in message

def testBasicAnnotation():
  sivm = get_ripl().sivm
  expr = v.app(v.sym("add"), v.num(1), v.sym("foo"))
  assert_annotation_succeeds(sivm.assume, v.sym("x"), expr)

def testBasicAnnotation2():
  ripl = get_ripl()
  assert_error_message_contains("""\
(add 1 foo)
       ^^^
""",
  ripl.assume, "x", "(+ 1 foo)")

def testAnnotateErrorTriggeredByInference():
  ripl = get_ripl()
  ripl.assume("control", "(flip)")
  ripl.force("control", True)
  ripl.predict("(if control 1 badness)")
  assert_error_message_contains("""\
(if control 1 badness)
^^^^^^^^^^^^^^^^^^^^^^
(if control 1 badness)
              ^^^^^^^
""",
  ripl.infer, "(mh default one 50)")

def testAnnotateProgrammaticAssume():
  ripl = get_ripl()
  assert_error_message_contains("""\
((assume x (add 1 foo)) model)
 ^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")
  assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")

def testAnnotateErrorTriggeredByInferenceOverProgrammaticAssume():
  # No do macro yet
  ripl = get_ripl()
  ripl.infer("(assume control (flip))")
  ripl.infer("(force control true)")
  ripl.infer("(predict (if control 1 badness))")
  # TODO Solve the double macroexpansion problem
  assert_error_message_contains("""\
((biplex control (make_csp (quote ()) (quote 1.0)) (make_csp (quote ()) (quote badness))))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
((biplex control (make_csp (quote ()) (quote 1.0)) (make_csp (quote ()) (quote badness))))
                                                                               ^^^^^^^
""",
  ripl.infer, "(mh default one 50)")

def testAnnotateDefinedProgrammaticAssume():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", "(lambda () (assume x (+ 1 foo)))")
  # Hm.  Blaming makers of inference actions rather than the actions
  # themselves produces this; which does point to the culprit.
  # However, the top stack frame is somewhat misleading as to when the
  # problem was identified.  I might be able to live with that.
  assert_error_message_contains("""\
((action) model)
 ^^^^^^^^
(lambda () (assume x (add 1 foo)))
           ^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(action)")
  assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(action)")

def testAnnotateInferenceProgramError():
  ripl = get_ripl()
  assert_error_message_contains("""\
((observe (normal 0 1) (add 1 foo)) model)
                              ^^^
""",
  ripl.infer, "(observe (normal 0 1) (+ 1 foo))")

def testAnnotateInferenceProgramErrorInDefinition():
  ripl = get_ripl(persistent_inference_trace=True)
  assert_error_message_contains("""\
(observe (normal 0 1) (add 1 foo))
                             ^^^
""",
  ripl.define, "badness", "(observe (normal 0 1) (+ 1 foo))")

def testAnnotateDefinedInferenceProgramError():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("badness", "(lambda () (observe (normal 0 1) (+ 1 foo)))")
  assert_error_message_contains("""\
((badness) model)
 ^^^^^^^^^
(lambda () (observe (normal 0 1) (add 1 foo)))
                                        ^^^
""",
  ripl.infer, "(badness)")

def testAnnotateDefinedQuasiquotedProgrammaticAssume():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", "(lambda (name) (assume x (+ 1 ,name)))")
  # Hm.  Blaming makers of inference actions rather than the actions
  # themselves produces this; which does point to the culprit.
  # However, the top stack frame is somewhat misleading as to when the
  # problem was identified.  I might be able to live with that.
  assert_error_message_contains("""\
((action (quote foo)) model)
 ^^^^^^^^^^^^^^^^^^^^
(lambda (name) (assume x (add 1 (unquote name))))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(action 'foo)")
  assert_error_message_contains("""\
(add 1.0 foo)
         ^^^
""",
  ripl.infer, "(action 'foo)")

def testAssignedDidUniqueness():
  ripl = get_ripl(persistent_inference_trace=True)
  for i in range(20):
    ripl.define("foo%d" % i, "(predict (normal 0 1))")
    ripl.infer("foo%d" % i)
  # Or maybe 60 if I start recording the infer statements too.
  eq_(40, len(ripl.sivm.syntax_dict.items()))

def testAnnotateInferenceErrorInDo():
  # TODO I need the inference trace to be persistent to trigger the
  # inference prelude did skipping hack :(
  ripl = get_ripl(persistent_inference_trace=True)
  expression = """\
(do (assume x (normal 0 1))
    (observe x (+ 1 badness)))"""
  assert_error_message_contains("""\
((do (assume x (normal 0 1)) (observe x (add 1 badness))) model)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
((do (assume x (normal 0 1)) (observe x (add 1 badness))) model)
                                               ^^^^^^^
""",
  ripl.infer, expression)

def testAnnotateInferenceErrorInDefinedDo():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("action", """\
(do (assume x (normal 0 1))
    (y <- (sample x))
    (observe x (+ 1 badness)))""")
  assert_error_message_contains("""\
(action model)
^^^^^^^^^^^^^^
(do (assume x (normal 0 1)) (y <- (sample x)) (observe x (add 1 badness)))
                                                                ^^^^^^^
""",
  ripl.infer, "action")
