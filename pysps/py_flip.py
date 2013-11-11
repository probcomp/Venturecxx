import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

import math
import random

class PyFlipSP(SP):

    def __init__(self):
        super(PyFlipSP, self).__init__()

    def pysp_output_simulate(self, args):
        theta = args[0]['value']
        val = (random.random() < theta)
        return {'type': 'boolean', 'value': val}

    def pysp_output_logdensity(self, args, val):
        print "calling flip density"
        theta = args[0]['value']
        if val['value']:
            return math.log(theta)
        else:
            return math.log(1.0 - theta)
        
def makeSP():
    return PyFlipSP()

def getSymbol():
    return "py_flip"

canAbsorb = True

isRandom = True
