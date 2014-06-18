# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import time
from venture.lite.utils import simulateCategorical

class Infer(object):
  def __init__(self, engine):
    self.engine = engine
    self.out = {}
    self.plot = None

  def _ensure_peek_name(self, name):
    if self.plot is not None:
      raise Exception("TODO Cannot plot and peek in the same inference program")
    if name in self.out: pass
    else: self.out[name] = []

  def _ensure_plot(self, spec, names, exprs):
    if len(self.out) > 0:
      raise Exception("TODO Cannot peek and plot in the same inference program")
    if self.plot is None:
      self.plot = SpecPlot(spec, names, exprs)
    elif spec == self.plot.spec_string and names == self.plot.names and exprs == self.plot.exprs:
      pass
    else:
      raise Exception("TODO Cannot plot with different specs in the same inference program")

  def infer(self, program):
    self.engine.incorporate()
    self.do_infer(program)
    return self.plot if self.plot is not None else self.out

  def do_infer(self, program):
    if 'command' in program and program['command'] == "resample":
      self.engine.resample(program['particles'])
    elif 'command' in program and program['command'] == "incorporate":
      pass
    elif 'command' in program and program['command'] == "peek":
      name = program['name']
      self._ensure_peek_name(name)
      value = self.engine.sample(program['expression'])
      self.out[name].append(value)
    elif 'command' in program and program['command'] == "plotf":
      self._ensure_plot(program["specification"], program["names"], program["expressions"])
      self.plot.add_data(self.engine)
    elif program['kernel'] == "cycle":
      if 'subkernels' not in program:
        raise Exception("Cycle kernel must have things to cycle over (%r)" % program)
      for _ in range(program["transitions"]):
        for k in program["subkernels"]:
          self.do_infer(k)
    elif program["kernel"] == "mixture":
      for _ in range(program["transitions"]):
        self.do_infer(simulateCategorical(program["weights"], program["subkernels"]))
    else: # A primitive infer expression
      self.engine.primitive_infer(program)

class SpecPlot(object):
  """Generate a plot according to a format specification.

  The format specifications are inspired loosely by the classic
  printf.  To wit, each individual plot that appears on a page is
  specified by some line noise consisting of format characters

  [<geom>]*((<stream>)?<scale>?){1,3}

  geoms: _p_oint, _l_ine, _b_ar, _h_istogram
  scales: _d_irect, _l_og
  streams: sweep _c_ounter, _t_ime (wall clock), <digits> that expression, 0-indexed, % (next), log _s_core (will be plotted double-log if on a log scale)

  TODO: Modifiers for how to treat multiple particles: distinguished
  (current implementation, good default), mean, median, all (what
  exactly would all mean?  2-D table? Splice and hope?)

  If one stream is indicated, it is taken as the y axis of the
  picture, and plotted against the sweep counter.  If two or more
  streams are indicated, the second is plotted on the y axis against
  the first.  If three streams are indicated, the third is mapped to
  color.

  """
  def __init__(self, spec, names, exprs):
    from plot_spec import PlotSpec
    self.spec_string = spec
    self.spec = PlotSpec(spec)
    self.names = names
    self.exprs = exprs
    self.data = dict([(name, []) for name in names + ["sweeps", "time (s)", "log score"]])
    self.sweep = 0
    self.time = time.time() # For sweep timing, should it be requested
    self.next_index = 0

  def add_data_from(self, engine, index):
    value = engine.sample(self.exprs[index])
    self.data[self.names[index]].append(value)
    self.next_index = index+1

  def add_data(self, engine):
    self.next_index = 0
    self.sweep += 1
    touched = set()
    for stream in self.spec.streams:
      if stream in touched:
        continue
      else:
        touched.add(stream)
      if stream == "c":
        self.data["sweeps"].append(self.sweep)
      elif stream == "t":
        self.data["time (s)"].append(time.time() - self.time)
      elif stream == "s":
        self.data["log score"].append(engine.logscore())
      elif stream == "" or stream == "%":
        self.add_data_from(engine, self.next_index)
      else:
        self.add_data_from(engine, int(stream))

  def __str__(self):
    "Not really a string method, but does get itself displayed when printed."
    for name in ["sweeps", "time (s)", "log score"] + self.names:
      if len(self.data[name]) == 0:
        # Data source was not requested; remove it to avoid confusing pandas
        del self.data[name]
    from ggplot import ggplot, aes
    from pandas import DataFrame
    from venture.ripl.ripl import _strip_types_from_dict_values
    dataset = DataFrame.from_dict(_strip_types_from_dict_values(self.data))
    plot = ggplot(dataset, aes(**self.aes_dict()))
    for geom in self.spec.geom:
      plot += geom
    print plot
    return "a plot"

  def aes_dict(self):
    next_index = 0
    ans = {}
    for (key, stream) in zip(["x", "y", "color"], self.spec.streams):
      if stream == "c":
        ans[key] = "sweeps"
      elif stream == "t":
        ans[key] = "time (s)"
      elif stream == "s":
        ans[key] = "log score"
      elif stream == "" or stream == "%":
        ans[key] = self.names[next_index]
        next_index += 1
      else:
        ans[key] = self.names[int(stream)]
        next_index = int(stream) + 1
    return ans
