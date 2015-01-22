import os.path
from venture.test.config import get_ripl

plugin_name = os.path.dirname(os.path.abspath(__file__)) + "/plugin.py"

def testPluginsLoad():
  r = get_ripl()
  r.load_plugin(plugin_name)
  r.infer("(call_back foo)")

def testPluginsLoad2():
  r = get_ripl()
  r.infer("(load_plugin (quote symbol<\"" + plugin_name + "\">))")
  r.infer("(call_back foo)")

def testPluginsLoad3():
  r = get_ripl()
  r.infer("""(do
  (seven <- (load_plugin (quote symbol<"%s">)))
  (assert (eq 7 seven)))""" % (plugin_name,))
