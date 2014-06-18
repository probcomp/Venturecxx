import re
import ggplot as g

stream_rx = r"([cts%]|[0-9]+)"
scale_rx = r"([dl])"
geom_rx = r"[plbah]"
toplevel_rx = "(" + geom_rx + "*)" + "((" + stream_rx + "?" + scale_rx + "?){1,3})$"
dimension_rx = stream_rx + "?" + scale_rx + "?"

class PlotSpec(object):
  def __init__(self, spec):
    self.two_d_only = True
    top = re.match(toplevel_rx, spec)
    if not top:
      raise Exception("Invalid plot spec %s; must match %s" % (spec, toplevel_rx))
    geoms = top.group(1)
    dims = top.group(2)
    self.geom = self._interp_geoms(geoms)
    if len(dims) == 0:
      raise Exception("Invalid plot spec %s; must supply at least one dimension to plot")
    self._interp_dimensions(dims)

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
    if len(gs) == 0:
      return [g.geom_point()]
    else:
      return [self._interp_geom(ge) for ge in gs]

  def _interp_geom(self, ge):
    if ge in ["b", "h"]:
      self.two_d_only = False
    return {"p":g.geom_point, "l":g.geom_line, "b":g.geom_bar, "h":g.geom_histogram}[ge]()

  def aes_dict(self, names):
    next_index = 0
    ans = {}
    for (key, stream) in zip(["x", "y", "color"], self.streams):
      if stream == "c":
        ans[key] = "sweeps"
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
    return ans
