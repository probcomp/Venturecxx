# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import re
from itertools import chain
from time import strftime

from venture.lite.utils import logWeightsToNormalizedDirect
from venture.lite.value import VentureString

stream_rx = r"([rcts%]|[0-9]+)"
scale_rx = r"([dl])"
geom_rx = r"[plbah]"
weight_rx = r"w?"
toplevel_rx = "(" + weight_rx + ")" + "(" + geom_rx + "*)" + "((" + stream_rx + "?" + scale_rx + "?){1,3})$"
dimension_rx = stream_rx + "?" + scale_rx + "?"

class PlotSpec(object):
  """A plot specification.

  See the documentation of plotf for the meanings of the possible specifiers.
  """
  def __init__(self, spec):
    if isinstance(spec, basestring):
      self.frames = [FrameSpec(spec)]
    elif isinstance(spec, VentureString):
      self.frames = [FrameSpec(spec.getString())]
    else:
      self.frames = [FrameSpec(s) for s in spec]

  def draw(self, dataset, names):
    import ggplot as g
    index = 0
    figs = []
    for spec in self.frames:
      spec.initialize()
      if spec.weighted:
        dataset['particle weight'] = logWeightsToNormalizedDirect(dataset['prt. log wgt.'])
      (aes, index) = spec.aes_dict_at(index, names, spec.get_geoms())
      plot = g.ggplot(dataset, g.aes(**aes))
      for geom in spec.get_geoms():
        plot += geom
      # add the wall time
      title = self._format_title(dataset)
      plot += g.ggtitle(title)
      for (dim, scale) in zip(spec.dimensions(), spec.scales):
        obj = self._interp_scale(dim, scale)
        if obj: plot += obj
      figs.append(self._add_date(plot.draw()))
    return figs

  def plot(self, dataset, names, filenames=None):
    import matplotlib.pylab as plt
    figs = self.draw(dataset, names)
    if filenames is None:
      plt.show()
      plt.close()
    else:
      for fig, filename in zip(figs, filenames):
        fig.suptitle(filename.replace('.png', ''))
        fig.savefig(filename)
      plt.close('all')
    # FIXME: add something to track names of frames here

  def streams(self):
    return chain(*[frame.streams for frame in self.frames])

  @staticmethod
  def _format_title(dataset):
    if 'time (s)' in dataset and 'iter' in dataset and 'prt. id' in dataset:
      walltime = dataset['time (s)'].max()
      niterations = dataset['iter'].max()
      nparticles = dataset['prt. id'].max() + 1
      title = 'Wall time: {0}m, {1:0.2f}s. Iterations: {2}. Particles: {3}'
      title = title.format(int(walltime // 60), walltime % 60, niterations, nparticles)
      return title
    else:
      return ""

  @staticmethod
  def _add_date(fig):
    fig.text(0.975, 0.025, strftime("%c"),
             horizontalalignment='right',
             verticalalignment='bottom')
    return fig

  def _interp_scale(self, dim, scale):
    import ggplot as g
    if scale == "d" or scale == "":
      if dim == "x":
        return g.scale_x_continuous()
      elif dim == "y":
        return g.scale_y_continuous()
      else:
        return None # TODO What's the "direct" color scale?
    else:
      assert scale == "l"
      if dim == "x":
        return g.scale_x_log()
      elif dim == "y":
        return g.scale_y_log()
      else:
        return None # TODO What's the "log" color scale?

class FrameSpec(object):
  def __init__(self, spec):
    self.spec_string = spec

  def initialize(self):
    spec = self.spec_string
    self.two_d_only = True
    top = re.match(toplevel_rx, spec)
    if not top:
      raise Exception("Invalid plot spec %s; must match %s" % (spec, toplevel_rx))
    self.weighted = top.group(1)
    self.geoms = top.group(2)
    dims = top.group(3)
    if len(dims) == 0:
      raise Exception("Invalid plot spec %s; must supply at least one dimension to plot")
    self._interp_geoms(self.geoms) # To set the self.two_d_only bit
    self._interp_dimensions(dims)

  def get_geoms(self):
    return self._interp_geoms(self.geoms)

  def _interp_dimensions(self, dims):
    self.streams = []
    self.scales = []
    for (stream, scale) in re.findall(dimension_rx, dims):
      if not(stream == "" and scale == ""):
        self.streams.append(stream)
        self.scales.append(scale)
    if len(self.streams) == 1 and self.two_d_only:
      # Two-dimensional plots default to plotting against iteration count (in direct space)
      self.streams = ["c"] + self.streams
      self.scales = ["d"] + self.scales

  def _interp_geoms(self, gs):
    import ggplot as g
    if len(gs) == 0:
      return [g.geom_point()]
    else:
      return [self._interp_geom(ge) for ge in gs]

  def _interp_geom(self, ge):
    import ggplot as g
    if ge in ["b", "h"]:
      self.two_d_only = False
    return {"p":g.geom_point, "l":g.geom_line, "b":g.geom_bar, "h":g.geom_histogram}[ge]()

  def dimensions(self):
    if self.two_d_only:
      return ["x", "y", "color"]
    else:
      return ["x", "color"]

  def aes_dict_at(self, next_index, names, geoms):
    next_index = next_index
    ans = {}
    for (key, stream) in zip(self.dimensions(), self.streams):
      if stream == "c":
        ans[key] = "iter"
      elif stream == "r":
        ans[key] = "prt. id"
      elif stream == "t":
        ans[key] = "time (s)"
      elif stream == "s":
        ans[key] = "log score"
      elif stream == "" or stream == "%":
        ans[key] = names[next_index]
        next_index += 1
      else:
        ans[key] = names[int(stream)]
        next_index = int(stream) + 1
    if self.weighted:
      from ggplot import geoms as g
      for geom in geoms:
        if isinstance(geom, g.geom_line) or isinstance(geom, g.geom_point):
          ans['alpha'] = 'particle weight'
        elif isinstance(geom, g.geom_histogram) or isinstance(geom, g.geom_bar):
          ans['weight'] = 'particle weight'
    return (ans, next_index)
