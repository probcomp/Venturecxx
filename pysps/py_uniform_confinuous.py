import sys
# FIXME: dlovell figure out if this is necessary
sys.path.append("../..")

from venture.cxx.libsp import SP

# FIXME: standardize on a policy for external random number generators and issues of reproducibility.
import random
import math

class UniformContinuousSP(SP):

    def __init__(self):
        super(UniformContinuousSP, self).__init__()

    def pysp_output_simulate(self, args):
        a = args[0]['value']
        b = args[1]['value']
        print "simulating on uniform with args" + str((a,b))

        val = a + (random.random() * (b - a))
        print "val: " + str(val)

        return {'type': 'number', 'value': val}

    def pysp_output_logdensity(self, args, val):
        print "calculating uniform density on value: " + str(val)
        return -1 * math.log(args[1]['value'] - args[0]['value'])
        
def makeSP():
    return UniformContinuousSP()

def getSymbol():
    return "py_uniform_continuous"

canAbsorb = True

isRandom = True
