import re
from itertools import chain

stream_rx = r"([rcts%]|[0-9]+)"
scale_rx = r"([dl])"
geom_rx = r"[plbah]"
toplevel_rx = "(" + geom_rx + "*)" + "((" + stream_rx + "?" + scale_rx + "?){1,3})$"
dimension_rx = stream_rx + "?" + scale_rx + "?"

class PlotSpec(object):
  def __init__(self, spec):
    if isinstance(spec, basestring):
      self.frames = [FrameSpec(spec)]
    else:
      self.frames = [FrameSpec(s) for s in spec]

  def draw(self, dataset, names):
    import ggplot as g
    index = 0
    figs = []
    for spec in self.frames:
      (aes, index) = spec.aes_dict_at(index, names)
      plot = g.ggplot(dataset, g.aes(**aes))
      for geom in spec.get_geoms():
        plot += geom
      for (dim, scale) in zip(["x", "y", "color"], spec.scales):
        obj = self._interp_scale(dim, scale)
        if obj: plot += obj
      figs.append(plot.draw())
    return figs

  def plot(self, dataset, names):
    import matplotlib.pylab as plt
    self.draw(dataset, names)
    plt.show()
    # FIXME: add something to track names of frames here

  def streams(self):
    return chain(*[frame.streams for frame in self.frames])

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
    self.two_d_only = True
    top = re.match(toplevel_rx, spec)
    if not top:
      raise Exception("Invalid plot spec %s; must match %s" % (spec, toplevel_rx))
    geoms = top.group(1)
    dims = top.group(2)
    self._geom = self._interp_geoms(geoms)
    if len(dims) == 0:
      raise Exception("Invalid plot spec %s; must supply at least one dimension to plot")
    self._interp_dimensions(dims)

  def get_geoms(self):
    return self._geom

  def _interp_dimensions(self, dims):
    self.streams = []
    self.scales = []
    for (stream, scale) in re.findall(dimension_rx, dims):
      if not(stream == "" and scale == ""):
        self.streams.append(stream)
        self.scales.append(scale)
    if len(self.streams) == 1 and self.two_d_only:
      # Two-dimensional plots default to plotting against sweep count (in direct space)
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

  def aes_dict_at(self, next_index, names):
    next_index = next_index
    ans = {}
    for (key, stream) in zip(["x", "y", "color"], self.streams):
      if stream == "c":
        ans[key] = "sweeps"
      elif stream == "r":
        ans[key] = "particle"
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
    return (ans, next_index)
