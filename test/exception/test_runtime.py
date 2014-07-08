from nose.tools import eq_, raises
from venture.test.config import get_ripl, backend
from testconfig import config
from nose import SkipTest
from venture.lite.exception import VentureError

@backend('lite')
@raises(VentureError)
def testSymbolNotFound():
  ripl = get_ripl()
  ripl.predict('a')
