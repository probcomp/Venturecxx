from venture.test.config import get_ripl
import venture.value.dicts as v
import numpy

def testVector():
  """Test that array-like objects don't get interpreted as expressions."""
  ripl = get_ripl()
  ripl.predict(v.vector(numpy.array([1, 2])))

