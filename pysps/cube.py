import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class CubeSP(SP):

  def __init__(self):
        super(CubeSP, self).__init__()

  def pysp_output_simulate(self,args):
    num = args[0]['value']
    return {'type': 'number', 'value': num * num * num}

  def pysp_output_logdensity(self,args, val):
    return 0.0

def makeSP():
  return CubeSP()

def getSymbol(): return "cube"

canAbsorb = False

isRandom = False
