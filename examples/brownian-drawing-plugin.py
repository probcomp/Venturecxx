# A custom inference SP for drawing the state of a particular model.

# The goal is to illustrate extending Venture with custom inference
# SPs, in this case one that offers a debugging display for a
# particular model.

# The model this applies to is
# [assume brown_step (gamma 1 1)]
# [assume obs_noise (gamma 1 1)]
# [assume position (mem (lambda (t) (scope_include (quote exp) t (if (<= t 0) (normal 0 brown_step) (normal (position (- t 1)) brown_step)))))]
# [assume obs_fun (lambda (t) (normal (position t) obs_noise))]
# [predict (position 10)]

# To use the drawing plugin, install it in the Venture interpreter by
# calling it with
#   -L brownian-drawing-plugin.py
# Then enjoy with
#   infer (cycle ((call_back (quote draw))) 10)

import pygame
pygame.init()
window = pygame.display.set_mode((640, 400))
pygame.display.update()

def draw(inferrer):
  window.fill(pygame.Color(255, 255, 255))

  # Draw the axis ticks
  for tick in [-8, -6, -4, -2, 0, 2, 4, 6, 8]:
    pygame.draw.line(window, pygame.Color(0, 0, 0), (0, y_to_pixels(tick)), (50, y_to_pixels(tick)), 1)

  alpha_level = 100

  # TODO Consider indicating the log score

  # Draw the motion speed levels
  brown_ys = ys_at(inferrer, "brown_step")
  for brown_y in brown_ys:
    dot = pygame.Surface((640, 400), pygame.SRCALPHA)
    dot.fill(pygame.Color(255, 255, 255, 0))
    pygame.draw.rect(dot, pygame.Color(0, 0, 255, alpha_level), (30, brown_y - 5, 10, 10), 2)
    window.blit(dot, (0,0))

  # Draw the observation noise levels
  obs_ys = ys_at(inferrer, "obs_noise")
  for obs_y in obs_ys:
    dot = pygame.Surface((640, 400), pygame.SRCALPHA)
    dot.fill(pygame.Color(255, 255, 255, 0))
    pygame.draw.rect(dot, pygame.Color(255, 0, 0, alpha_level), (15, obs_y - 5, 10, 10), 2)
    window.blit(dot, (0,0))

  # Plot the observations and decide how far to plot the trajectory
  plot_range = 2
  for (_did, directive) in inferrer.engine.directives.items():
    if directive[0] == "observe":
      (_, datum, val) = directive
      obs_i = int(datum[1]["value"])
      x = x_to_pixels(obs_i)
      y = y_to_pixels(val["value"])
      pygame.draw.circle(window, pygame.Color(255, 0, 0), (x, y), 4, 0)
      plot_range = max(plot_range, obs_i + 1)
    if directive[0] == "predict":
      (_, datum) = directive
      pr_i = int(datum[1]["value"])
      plot_range = max(plot_range, pr_i + 1)

  point_lists = [points_at(inferrer, i) for i in range(plot_range)]
  from pygame.locals import BLEND_ADD
  for p in range(len(point_lists[0])):
    path = pygame.Surface((640, 400), pygame.SRCALPHA)
    path.fill(pygame.Color(255, 255, 255, 0))
    for i in range(1, plot_range):
      (x_p, y_p) = point_lists[i-1][p]
      (x_n, y_n) = point_lists[i][p]
      pygame.draw.line(path, pygame.Color(0, 0, 255, alpha_level), (x_p, y_p), (x_n, y_n), 3)
    window.blit(path, (0,0))

  # for i in range(1, plot_range):
  #   old_ps = points_at(inferrer, i-1)
  #   new_ps = points_at(inferrer, i)
  #   for ((x_p, y_p), (x_n, y_n)) in zip(old_ps, new_ps):
  #     pygame.draw.line(window, pygame.Color(255, 0, 0, 1), (x_p, y_p), (x_n, y_n), 3)
  pygame.display.update()

def ys_at(inferrer, var):
  import venture.value.dicts as val
  return [y_to_pixels(y["value"]) for y in inferrer.engine.sample_all(val.sym(var))]

def points_at(inferrer, i):
  import venture.value.dicts as val
  return [(x_to_pixels(i), y_to_pixels(y["value"])) for y in inferrer.engine.sample_all([val.sym("position"), val.num(i)])]

def y_to_pixels(model_y):
  return int(200 - 30 * model_y)
def x_to_pixels(model_x):
  return int(60 + 30 * model_x)

def stop_drawing(_inferrer):
  pygame.quit()

def __venture_start__(ripl):
  ripl.bind_callback("draw", draw)
  ripl.bind_callback("stop_drawing", stop_drawing)
