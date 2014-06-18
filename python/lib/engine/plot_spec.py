import re
import ggplot as g

stream_rx = r"([cts%]|[0-9]+)"
scale_rx = r"([dl])"
geom_rx = r"[plbah]"
toplevel_rx = "(" + geom_rx + "*)" + "((" + stream_rx + "?" + scale_rx + "?){1,3})$"
dimension_rx = stream_rx + "?" + scale_rx + "?"

class PlotSpec(object):
  def __init__(self, spec):
    top = re.match(toplevel_rx, spec)
    if not top:
      raise Exception("Invalid plot spec %s; must match %s" % (spec, toplevel_rx))
    geoms = top.group(1)
    dims = top.group(2)
    self.geom = _interp_geoms(geoms)
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
    if len(self.streams) == 1:
      # Default to plotting against sweep count (in direct space)
      self.streams = ["c"] + self.streams
      self.scales = ["d"] + self.scales

def _interp_geoms(gs):
  if len(gs) == 0:
    return [g.geom_point()]
  else:
    return [_interp_geom(ge) for ge in gs]

def _interp_geom(ge):
  return {"p":g.geom_point, "l":g.geom_line, "b":g.geom_bar, "h":g.geom_histogram}[ge]()
