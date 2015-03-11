from nose.tools import assert_raises

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
(assume x (add 1 foo))
^^^^^^^^^^^^^^^^^^^^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")
  assert_error_message_contains("""\
(add 1.0 foo)
^^^^^^^^^^^^^
""",
  ripl.infer, "(assume x (+ 1 foo))")
