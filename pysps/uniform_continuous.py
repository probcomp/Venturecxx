import sys
# FIXME: dlovell figure out if this is necessary
sys.path.append("../..")

from venture.cxx.libsp import SP

# FIXME: standardize on a policy for external random number generators and issues of reproducibility.
import random

class UniformContinuousSP(SP):

    def __init__(self):
        super(UniformContinuousSP, self).__init__()

    def simulate(self, args):
        a = args[0]
        b = args[1]

        return a + (random.random() * (b - a))

    def logDensity(self, args, val):
        return -1 * math.log(b - a)
        
def makeSP():
    return UniformContinuousSP()

def getSymbol():
    return "uniform_continuous"

