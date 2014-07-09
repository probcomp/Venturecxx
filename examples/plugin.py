# A custom inference SP to make Vikash happy

import venture.lite.psp as psp
import venture.lite.value as v
from venture.lite.builtin import typed_nr

import pygame
pygame.init()
window = pygame.display.set_mode((640, 400))
pygame.display.update()

class DrawFramePSP(psp.RandomPSP):
  "In the inference language, this will be usable as a raw symbol (no parameters)"
  def __init__(self, window):
    self.window = window
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  def simulate(self, args):
    inferrer = args.operandValues[0]
    import pygame
    import random
    self.window.fill(pygame.Color(255, 255, 255))
    for _ in range(10):
      pygame.draw.circle(self.window, pygame.Color(255, 0, 0), (int(random.uniform(30, 610)), int(random.uniform(30, 370))), 20, 0)
    pygame.display.update()
    return inferrer

draw_sp = typed_nr(DrawFramePSP(window), [v.ForeignBlobType()], v.ForeignBlobType())

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
