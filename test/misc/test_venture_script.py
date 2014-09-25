from nose.tools import raises
from venture.test.config import get_ripl
from venture.exception import VentureException

def testVentureScriptProgram():
  """At one point execute_program crashed with VentureScript."""
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("assume a = proc() {1}")

def testVentureScriptUnparseExpException():
  """At one point execute_program crashed with VentureScript."""
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  try:
    ripl.execute_program("assume a = lambda")
  except VentureException as e:
    assert(e.exception == "text_parse")
  else:
    assert(False, "lambda is illegal in VentureScript and should raise a text_parse exception.")
