# Copyright (c) 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import pygame
import pygame.image
import numbers

import venture.ripl.utils as u
import venture.value.dicts as v
from venture.exception import VentureException

class Draw(object):
  def __init__(self):
    self.winsize = (750,750)
    self.view_x = (-10.0, 10.0)
    self.view_y = (-10.0, 10.0)
    self.win_x = (0.0, self.winsize[0])
    self.win_y = (0.0, self.winsize[1])
    self._do_start()

  def _do_start(self):
    pygame.init()
    self.window = pygame.display.set_mode(self.winsize)
    pygame.display.update()

  def _ensure_started(self):
    if self.window is None:
      self._do_start()

  def draw(self, inferrer, alpha_levels=None):
    self._ensure_started()
    self.window.fill(pygame.Color(255, 255, 255))
    if alpha_levels is None:
      n = len(inferrer.particle_log_weights())
      alpha_levels = [max(int(255.0 / n), 100) for _ in range(n)]  # Blend the particles evenly by default
    (has_quad, has_sine) = self._draw_observations(inferrer)
    if has_sine:
      self._draw_curves_by_sampling_points(inferrer, alpha_levels)
    else: # Faster, if you can use it; especially against Lite
      self._draw_curves_by_sampling_parameters(inferrer, has_quad, alpha_levels)
    pygame.display.update()

  def wdraw(self, inferrer):
    alpha_levels = [int(255.0 * p) for p in inferrer.particle_normalized_probs()]
    self.draw(inferrer, alpha_levels)

  def draw_to_disk(self, inferrer, paths):
    path = paths[0]["value"]
    self.draw(inferrer)
    pygame.image.save(self.window, path)

  def stop(self, _inferrer):
    pygame.quit()
    self.window = None

  def _draw_observations(self, inferrer):
    has_quad = False
    has_sine = False
    try:
        noise_level = u.strip_types(inferrer.engine.sample(v.sym("noise")))
    except VentureException:
        noise_level = 1 # Assume that undefined noise means 1
    for (_did, directive) in inferrer.engine.getDistinguishedTrace().directives.items():
      if directive[0] == "define":
        (_, symbol, datum) = directive
        if symbol == "is_quadratic":
          has_quad = True
        if symbol == "has_sine":
          has_sine = True
      if directive[0] == "observe":
        (_, datum, val) = directive
        if isinstance(datum, list) and len(datum) == 2:
          # Assume obs_fun call with no outlier tag
          if isinstance(datum[1], list) and len(datum[1]) == 2 and datum[1][0] == {'type': 'symbol', 'value': 'quote'}:
            # quoted, probably by observe_dataset
            obs_x = datum[1][1]["value"]
          else:
            obs_x = datum[1]["value"]
          is_outlier = False
        elif isinstance(datum, list):
          # Assume obs_fun call with outlier tag
          # Assume outliers are not vectorized
          id = datum[1]
          is_outlier = u.strip_types(inferrer.engine.sample(v.app(v.sym("is_outlier"), id)))
          if isinstance(datum[2], list) and len(datum[2]) == 2 and datum[2][0] == {'type': 'symbol', 'value': 'quote'}:
            # quoted, probably by observe_dataset
            obs_x = datum[2][1]["value"]
          else:
            obs_x = datum[2]["value"]
        if isinstance(datum, list):
          if isinstance(obs_x, numbers.Number):
            # This is the one-observation-at-a-time regime
            self._draw_point((int(obs_x), val["value"]), is_outlier, noise_level)
          else:
            # This is the vectorized observation regime
            for (x, y) in zip(obs_x, val["value"]):
              self._draw_point((int(x), y), is_outlier, noise_level)
    return (has_quad, has_sine)

  def _draw_curves_by_sampling_parameters(self, inferrer, has_quad, alpha_levels):
    intercepts = u.strip_types(inferrer.engine.sample_all(v.sym("intercept")))
    slopes = u.strip_types(inferrer.engine.sample_all(v.sym("slope")))
    if has_quad:
      quads = u.strip_types(inferrer.engine.sample_all(v.sym("c")))
      is_quadratics = u.strip_types(inferrer.engine.sample_all(v.sym("is_quadratic")))
    else:
      quads = [0 for _ in range(len(intercepts))]
      is_quadratics = [False for _ in range(len(intercepts))]
    for (is_quadratic, quad, slope, intercept, alpha_level) in zip(is_quadratics, quads, slopes, intercepts, alpha_levels):
      if alpha_level == 0: continue
      if is_quadratic:
        self._draw_curve(quad, slope, intercept, alpha_level)
      else:
        self._draw_line(slope, intercept, alpha_level)

  def _draw_curves_by_sampling_points(self, inferrer, alpha_levels):
    surface = pygame.Surface(self.winsize, pygame.SRCALPHA)
    surface.fill(pygame.Color(255, 255, 255, 0))
    def ev(x):
      vals = u.strip_types(inferrer.engine.sample_all(v.app(v.sym("f"), v.num(x))))
      return [(x, val) for val in vals]
    fidelity = 3
    curves = zip(*[ev(x/float(fidelity)-10) for x in range(20 * fidelity + 1)])
    for curve, alpha_level in zip(curves, alpha_levels):
      pygame.draw.lines(surface, _blue(alpha_level), False, [self._interpolate_pt(p) for p in curve])
    self.window.blit(surface, (0,0))

  def _draw_point(self, pt, is_outlier, noise_level):
    point = pygame.Surface(self.winsize, pygame.SRCALPHA)
    point.fill(pygame.Color(255, 255, 255, 0))
    if is_outlier:
      color = _gray(255)
    else:
      color = _green(255)
    pygame.draw.circle(point, color, _as_int(self._interpolate_pt(pt)), 5)
    top = _shift(pt, (0, -noise_level * 2))
    bot = _shift(pt, (0, noise_level * 2))
    pygame.draw.line(point, color, self._interpolate_pt(bot), self._interpolate_pt(top))
    self.window.blit(point, (0,0))

  def _draw_line(self, slope, intercept, alpha_level):
    ray = pygame.Surface(self.winsize, pygame.SRCALPHA)
    ray.fill(pygame.Color(255, 255, 255, 0))
    self._do_draw_line(ray, slope, intercept, alpha_level)
    self.window.blit(ray, (0,0))

  def _do_draw_line(self, surface, slope, intercept, alpha_level):
    if abs(slope) < 1:
      left_intercept = -10 * slope + intercept
      right_intercept = 10 * slope + intercept
      start = (-10, left_intercept)
      end = (10, right_intercept)
    else:
      top_intercept = (10 - intercept)/slope  # x*slope + intercept = 10
      bot_intercept = (-10 - intercept)/slope # x*slope + intercept = -10
      start = (top_intercept, 10)
      end = (bot_intercept, -10)
    pygame.draw.line(surface, _blue(alpha_level), self._interpolate_pt(start), self._interpolate_pt(end))

  def _draw_curve(self, quad, slope, intercept, alpha_level):
    ray = pygame.Surface(self.winsize, pygame.SRCALPHA)
    ray.fill(pygame.Color(255, 255, 255, 0))
    self._do_draw_curve(ray, quad, slope, intercept, alpha_level)
    self.window.blit(ray, (0,0))

  def _do_draw_curve(self, surface, quad, slope, intercept, alpha_level):
    def ev(x):
      return quad * x * x + slope * x + intercept
    pts = [(x-10,ev(x-10)) for x in range(21)]
    pygame.draw.lines(surface, _blue(alpha_level), False, [self._interpolate_pt(p) for p in pts])

  def _interpolate_pt(self, pt):
    (x,y) = pt
    return (self._interpolate_x(x), self._interpolate_y(y))

  def _interpolate_x(self, x):
    return _interpolate(x, self.view_x, self.win_x)

  def _interpolate_y(self, y):
    # invert y, because graphics coordinates.
    return _interpolate(-y, self.view_y, self.win_y)

def _interpolate(src_pt, src_bounds, dest_bounds):
  src_offset = src_pt - src_bounds[0]
  scale = (dest_bounds[1] - dest_bounds[0]) / (src_bounds[1] - src_bounds[0])
  return dest_bounds[0] + src_offset * scale

def _shift(pt, disp):
  (pt_x, pt_y) = pt
  (disp_x, disp_y) = disp
  return (pt_x + disp_x, pt_y + disp_y)

def _as_int(pt):
  return (int(pt[0]), int(pt[1]))

def _red(alpha_level):
  return pygame.Color(255,0,0,alpha_level)

def _gray(alpha_level):
  return pygame.Color(200,200,200,alpha_level)

def _green(alpha_level):
  return pygame.Color(0,255,0,alpha_level)

def _blue(alpha_level):
  return pygame.Color(0,0,255,alpha_level)

def __venture_start__(ripl):
  draw = Draw()
  ripl.bind_methods_as_callbacks(draw)
