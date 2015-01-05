import os.path
from venture.test.config import get_ripl

def testPluginsLoad():
  r = get_ripl()
  r.load_plugin(os.path.dirname(os.path.abspath(__file__)) + "/plugin.py")
  r.infer("(call_back foo)")
