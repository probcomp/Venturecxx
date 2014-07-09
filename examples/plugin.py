# A custom inference SP to make Vikash happy

import venture.lite.psp as psp
import venture.lite.value as v
from venture.lite.builtin import typed_nr

import pygame
pygame.init()
windowSurfaceObj = pygame.display.set_mode((640, 400))
pygame.display.update()

class DrawFramePSP(psp.RandomPSP):
  "In the inference language, this will be usable as a raw symbol (no parameters)"
  def __init__(self): pass
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    inferrer = args.operandValues[0]
    print 9
    return inferrer

draw_sp = typed_nr(DrawFramePSP(), [v.ForeignBlobType()], v.ForeignBlobType())

class QuitPSP(psp.RandomPSP):
  "In the inference language, this will be usable as a raw symbol (no parameters)"
  def __init__(self): pass
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    inferrer = args.operandValues[0]
    print 8
    import pygame
    pygame.quit()
    return inferrer

quit_sp = typed_nr(QuitPSP(), [v.ForeignBlobType()], v.ForeignBlobType())

self.ripl.bind_foreign_inference_sp("draw", draw_sp)
self.ripl.bind_foreign_inference_sp("stop", quit_sp)

# Install me at the Venture prompt with
#   eval execfile("examples/plugin.py")
# Then enjoy with
#   infer (cycle (draw) 10)
