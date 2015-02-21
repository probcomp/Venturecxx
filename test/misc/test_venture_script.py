from venture.test.config import get_ripl, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete
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
    assert e.exception == "text_parse"
  else:
    assert False, "lambda is illegal in VentureScript and should raise a text_parse exception."

@statisticalTest
def testVentureScriptLongerProgram():
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("assume is_tricky = flip(0.25) // end of line comments work\nassume coin_weight = if (is_tricky)\n{ uniform_continuous(0, 1) } \nelse {0.5}")
  ripl.predict("flip(coin_weight)", label="pid")
  ans = [(True, 0.5), (False, 0.5)]
  predictions = collectSamples(ripl, "pid", infer="10")
  return reportKnownDiscrete(ans, predictions)
