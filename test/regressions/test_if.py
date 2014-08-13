from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("mh")
def testIf1():
  """This caused an earlier CXX implementation to crash because of a
  corner case of operators changing during inference."""
  ripl = get_ripl()
  ripl.assume('IF', '(quote branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(10)

@on_inf_prim("mh")
def testIf2():
  "More extended version of testIf1"
  ripl = get_ripl()
  ripl.assume('if1', '(if (bernoulli 0.5) branch branch)')
  ripl.assume('if2', '(if (bernoulli 0.5) if1 if1)')
  ripl.assume('if3', '(if (bernoulli 0.5) if2 if2)')
  ripl.assume('if4', '(if (bernoulli 0.5) if3 if3)')
  ripl.infer(20)
