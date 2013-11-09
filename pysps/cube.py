import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class CubeSP(SP):

  def __init__(self):
        super(CubeSP, self).__init__()

  def simulate(self,args):
    value = args[0] * args[0] * args[0]
    return {'type': 'number', 'value': value}

  def logDensity(self,args, val):
    return 0.0

def makeSP():
  return CubeSP()

def getSymbol(): return "cube"
