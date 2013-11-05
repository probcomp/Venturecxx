#!/usr/bin/python

import sys
sys.path.append(".")
sys.path.append("inc/pysps") 

from libtrace import Trace

t = Trace()
t.eval(1, {"type":"number","value":4.0})
t.eval(2, [{"type":"symbol","value":"plus"},{"type":"number","value":5.0},{"type":"number","value":6.0}])
t.eval(3, {"type":"boolean","value":True})
t.eval(4, {"type":"atom","value":2})
t.eval(5, [{"type":"symbol","value":"categorical"},
           {"type":"number","value":1.0},
           {"type":"number","value":1.0}
       ])

print t.extractValue(1)
print t.extractValue(2)
print t.extractValue(3)
print t.extractValue(4)
print t.extractValue(5)
