from venture.test.config import get_ripl

def testVentureScriptProgram():
  """At one point execute_program crashed with VentureScript."""
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("assume a = proc() {1}")

