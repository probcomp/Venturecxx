import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class loadImage(SP):

  def __init__(self):
    sys.path.append("../../NIPS2013Vision")
    import _vision_things
    self.vt = _vision_things
    super(loadImage, self).__init__()

  def pysp_output_simulate(self,args):
    self.vt._vision_initialized_renderer.loadImage(args[1]['value'])
    return {'type': 'number', 'value': 0.0}

  def pysp_output_logdensity(self,args, val):
    return 0.0

def makeSP():
  return loadImage()

def getSymbol(): return "loadImage"

canAbsorb = False

isRandom = False
