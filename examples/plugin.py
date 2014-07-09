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
    self.window.fill(pygame.Color(255, 255, 255))
    brown_y = self.y_to_pixels(inferrer.engine.sample(self.sym("brown_step"))["value"])
    pygame.draw.rect(self.window, pygame.Color(0, 255, 0), (30, brown_y, 10, 10), 2)
    obs_y = self.y_to_pixels(inferrer.engine.sample(self.sym("obs_noise"))["value"])
    pygame.draw.rect(self.window, pygame.Color(0, 0, 255), (15, obs_y, 10, 10), 2)
    for i in range(10):
      x = int(60 + 30 * i)
      y = self.y_to_pixels(inferrer.engine.sample([self.sym("position"), self.num(i)])["value"])
      pygame.draw.circle(self.window, pygame.Color(255, 0, 0), (x, y), 10, 0)
    pygame.display.update()
    return inferrer

  def y_to_pixels(self, model_y):
    return int(200 - 30 * model_y)

  def sym(self, s):
    return {"type":"symbol", "value":s}
  def num(self, i):
    return {"type":"number", "value":i}

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
