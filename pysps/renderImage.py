import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class renderImage(SP):

  def __init__(self):
    sys.path.append("../../NIPS2013Vision")
    import _vision_things
    self.vt = _vision_things
    super(renderImage, self).__init__()

  def pysp_output_simulate(self,args):
    #this is a big hack
    self.vt._incremental_id = self.vt._incremental_id + 1                
    
    passing_args = []
    for i in range(0, len(args)):
      passing_args.append(args[i]['value'])
    self.vt._vision_initialized_renderer.get_rendered_image(passing_args,imageid=self.vt._incremental_id)
    return {'type': 'number', 'value': self.vt._incremental_id}

  def pysp_output_logdensity(self, args, val):
    return 0.0

def makeSP():
  return renderImage()

def getSymbol(): return "renderImage"

canAbsorb = False

isRandom = False
