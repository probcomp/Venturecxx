from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim

class TestArrayExtended(object):
  _multiprocess_can_split_ = True
  def setup(self):
    self.ripl = get_ripl()
    self.ripl.assume("xs","(array 11 22 33)")

  @on_inf_prim("none")
  def testLookup(self):
    assert self.ripl.predict("(lookup xs 0)") == 11
    assert self.ripl.predict("(lookup xs 1)") == 22
    assert self.ripl.predict("(lookup xs 2)") == 33

  @on_inf_prim("none")
  def testLength(self):
    assert self.ripl.predict("(size xs)") == 3

  @on_inf_prim("none")
  def testIsArray(self):
    assert self.ripl.predict("(is_array xs)")
    assert self.ripl.predict("(is_array (array))")
    assert not self.ripl.predict("(is_array (list 1 2))")
    assert not self.ripl.predict("(is_array 0)")

  @on_inf_prim("none")
  def testSize(self):
    assert self.ripl.predict("(size xs)") == 3

@gen_on_inf_prim("none")
def testMatrix():
  for form in ["(matrix (array))", "(matrix (array (array) (array)))",
               "(matrix (array (array 1 0) (array 0 1)))"]:
    yield checkMatrix, form

def checkMatrix(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_matrix %s)" % form)

@gen_on_inf_prim("none")
def testSimplex():
  for form in ["(simplex)", "(simplex 1)", "(simplex 0.2 0.8)"]:
    yield checkSimplex, form

def checkSimplex(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_simplex %s)" % form)

@on_inf_prim("none")
def testSimplexSize():
  assert get_ripl().predict("(size (simplex 0.3 0.7))") == 2

@on_inf_prim("none")
def testSimplexEq():
  assert get_ripl().predict("(= (simplex 0.5 0.5) (simplex 0.5 0.5))")
  assert not get_ripl().predict("(= (simplex 0.5 0.5) (simplex 0.4 0.6))")
