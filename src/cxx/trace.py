#!/usr/bin/python

import sys
sys.path.append(".")

from libtrace import Trace

t = Trace()
t.evalExpression("1",["float_plus",1.0,1.0])
print t.getDouble("1")
