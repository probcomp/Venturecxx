#!/usr/bin/python

import sys
sys.path.append(".")

from libtrace import Trace

t = Trace()
t.eval("1",["biplex","false",["float_plus",1.0,1.0],["float_plus",2.0,2.0]])
print t.extractValue("1")
