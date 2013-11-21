import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class noiseImageCompare(SP):

  def __init__(self):
    sys.path.append("../../NIPS2013Vision")
    import _vision_things
    self.vt = _vision_things
    super(noiseImageCompare, self).__init__()

  def pysp_output_simulate(self,args):
    return {'type': 'boolean', 'value': True}

  def pysp_output_logdensity(self, args, val):
    return self.vt._vision_initialized_renderer.getLogLikelihood(args[1]['value'],args[2]['value'])

def makeSP():
  return noiseImageCompare()

def getSymbol(): return "noiseImageCompare"

canAbsorb = True

isRandom = True
