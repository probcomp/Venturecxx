from venture.test.config import get_ripl

class TestArrayExtended(object):
  _multiprocess_can_split_ = True
  def setup(self):
    self.ripl = get_ripl()
    self.ripl.assume("xs","(array 11 22 33)")

  def testLookup(self):
    assert self.ripl.predict("(lookup xs 0)") == 11
    assert self.ripl.predict("(lookup xs 1)") == 22
    assert self.ripl.predict("(lookup xs 2)") == 33

  def testLength(self):
    assert self.ripl.predict("(size xs)") == 3

  def testIsArray(self):
    assert self.ripl.predict("(is_array xs)")
    assert self.ripl.predict("(is_array (array))")
    assert not self.ripl.predict("(is_array (list 1 2))")
    assert not self.ripl.predict("(is_array 0)")

  def testSize(self):
    assert self.ripl.predict("(size xs)") == 3

def testMatrix():
  for form in ["(matrix (list))", "(matrix (list (list) (list)))",
               "(matrix (list (list 1 0) (list 0 1)))"]:
    yield checkMatrix, form

def checkMatrix(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_matrix %s)" % form)

def testSimplex():
  for form in ["(simplex)", "(simplex 1)", "(simplex 0.2 0.8)"]:
    yield checkSimplex, form

def checkSimplex(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_simplex %s)" % form)

def testSimplexSize():
  assert get_ripl().predict("(size (simplex 0.3 0.7))") == 2
