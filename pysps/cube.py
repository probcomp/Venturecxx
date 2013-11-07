import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class CubeSP(SP):

  def __init__(self):
        super(CubeSP, self).__init__()

  def simulate(self,args):
    return args[0] * args[0] * args[0]

def makeSP():
  return CubeSP()

def getSymbol(): return "cube"
