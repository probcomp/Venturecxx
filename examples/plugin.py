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
    for tick in [-2, -1, 0, 1, 2]:
      pygame.draw.line(self.window, pygame.Color(0, 0, 0), (0, self.y_to_pixels(tick)), (50, self.y_to_pixels(tick)), 1)
    brown_ys = self.ys_at(inferrer, "brown_step")
    for brown_y in brown_ys:
      pygame.draw.rect(self.window, pygame.Color(0, 255, 0), (30, brown_y - 5, 10, 10), 2)
    obs_ys = self.ys_at(inferrer, "obs_noise")
    for obs_y in obs_ys:
      pygame.draw.rect(self.window, pygame.Color(0, 0, 255), (15, obs_y - 5, 10, 10), 2)
    plot_range = 2
    for (_did, directive) in inferrer.engine.directives.items():
      if directive[0] == "observe":
        (_, datum, val) = directive
        obs_i = int(datum[1]["value"])
        x = self.x_to_pixels(obs_i)
        y = self.y_to_pixels(val["value"])
        pygame.draw.circle(self.window, pygame.Color(155, 155, 0), (x, y), 10, 0)
        plot_range = max(plot_range, obs_i + 1)
      if directive[0] == "predict":
        (_, datum) = directive
        pr_i = int(datum[1]["value"])
        plot_range = max(plot_range, pr_i + 1)
    for i in range(1, plot_range):
      old_ps = self.points_at(inferrer, i-1)
      new_ps = self.points_at(inferrer, i)
      for ((x_p, y_p), (x_n, y_n)) in zip(old_ps, new_ps):
        pygame.draw.line(self.window, pygame.Color(255, 0, 0), (x_p, y_p), (x_n, y_n), 3)
    pygame.display.update()
    return inferrer

  def ys_at(self, inferrer, var):
    return [self.y_to_pixels(y["value"]) for y in inferrer.engine.sample_all(self.sym(var))]

  def points_at(self, inferrer, i):
    return [(self.x_to_pixels(i), self.y_to_pixels(y["value"])) for y in inferrer.engine.sample_all([self.sym("position"), self.num(i)])]

  def y_to_pixels(self, model_y):
    return int(200 - 30 * model_y)
  def x_to_pixels(self, model_x):
    return int(60 + 30 * model_x)

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
