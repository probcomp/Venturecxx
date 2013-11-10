import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

import random

class PyFlipSP(SP):

    def __init__(self):
        super(PyFlipSP, self).__init__()

    def simulate(self, args):
        theta = args[0]
        val = (random.random() < theta)
        return {'type': 'boolean', 'value': val}

    def logDensity(self, args, val):
        theta = args[0]
        if val:
            return math.log(theta)
        else:
            return math.log(1.0 - theta)
        
def makeSP():
    return PyFlipSP()

def getSymbol():
    return "pyflip"
