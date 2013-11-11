import sys
sys.path.append("../..")

import math

from venture.cxx.libsp import SP

class SquareSP(SP):

  def __init__(self):
        super(SquareSP, self).__init__()

  def pysp_output_simulate(self,args):
    num = args[0]['value']
    print "square: simulating on: " + str(num)
    out = {'type': 'number', 'value': num * num}
    print "square: returning: " + str(out)
    return out

  def pysp_output_logdensity(self,args,val):
    print "square: calling logdensity on val " + str(val) + " with args " + str(args)
    return 0.0

def makeSP():
  return SquareSP()

def getSymbol(): return "square"

canAbsorb = False
isRandom = False
