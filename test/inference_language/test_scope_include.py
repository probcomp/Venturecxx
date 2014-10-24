from venture.test.config import get_ripl, broken_in

@broken_in('lite', "lite can't handle arrays as blocks in a scope_include.")
def testArrayBlock():
  ripl = get_ripl()
  
  ripl.predict('(scope_include 1 (array 1 1) 0)')
