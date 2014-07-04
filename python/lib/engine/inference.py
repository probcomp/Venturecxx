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
    elif 'command' in program and program['command'] == "peek-all":
      name = program['name']
      self._ensure_peek_name(name)
      values = self.engine.sample_all(program['expression'])
      self.out[name].append(values)
    elif 'command' in program and program['command'] == "plotf":
      self._ensure_plot(program["specification"], program["names"], program["expressions"])
      self.plot.add_data(self.engine)
    elif 'command' in program and program['command'] == "loop":
      # TODO Assert that loop is only done at the top level?
      params = {"kernel":"cycle", "subkernels":program["kernels"], "in_python":True, "transitions":1}
      self.engine.start_continuous_inference(params)
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

  def infer_exp(self, program):
    self.engine.incorporate()
    self.do_infer_exp(program)
    return self.plot if self.plot is not None else self.out

  def do_infer_exp(self, exp):
    def default_name_for_exp(exp):
      if isinstance(exp, basestring):
        return exp
      elif hasattr(exp, "__iter__"):
        return "(" + ' '.join([default_name_for_exp(e) for e in exp]) + ")"
      else:
        return str(exp)
    operator = exp[0]
    if operator == "resample":
      assert len(exp) == 2
      self.engine.resample(exp[1])
    elif operator == "incorporate":
      assert len(exp) == 1
    elif operator in ["peek", "peek-all"]:
      assert 2 <= len(exp) and len(exp) <= 3
      if len(exp) == 3:
        (_, expression, name) = exp
      else:
        (_, expression) = exp
      name = default_name_for_exp(expression)
      self._ensure_peek_name(name)
      if operator == "peek":
        value = self.engine.sample(expression)
        self.out[name].append(value)
      else:
        values = self.engine.sample_all(expression)
        self.out[name].append(values)
    elif operator == "plotf":
      assert len(exp) >= 2
      spec = exp[1]
      exprs = exp[2:]
      names = [default_name_for_exp(e) for e in exprs]
      self._ensure_plot(spec, names, exprs)
      self.plot.add_data(self.engine)
    elif operator == "loop":
      # TODO Assert that loop is only done at the top level?
      assert len(exp) == 2
      (_, subkernels) = exp
      prog = ["cycle", subkernels, 1]
      self.engine.start_continuous_inference_exp(prog, in_python=True)
    elif operator == "cycle":
      assert len(exp) == 3
      (_, subkernels, transitions) = exp
      assert type(subkernels) is list
      for _ in range(transitions):
        for k in subkernels:
          self.do_infer(k)
    elif operator == "mixture":
      assert len(exp) == 3
      (_, weighted_subkernels, transitions) = exp
      assert type(weighted_subkernels) is list
      weights = []
      subkernels = []
      for i in range(len(weighted_subkernels)/2):
        j = 2*i
        k = j + 1
        weights.append(weighted_subkernels[j])
        subkernels.append(weighted_subkernels[k])
      for _ in range(transitions):
        self.do_infer(simulateCategorical(weights, subkernels))
    else: # A primitive infer expression
      self.engine.primitive_infer(exp)

class SpecPlot(object):
  """(plotf spec exp0 ...) -- Generate a plot according to a format specification.

  Example:
    [INFER (cycle ((mh default one 1) (plotf c0s x)) 1000)]
  will do 1000 iterations of MH and then show a plot of the x variable
  (which should be a scalar) against the sweep number (from 1 to
  1000), colored according to the global log score.

  Example library use:
    ripl.infer("(cycle ((mh default one 1) (plotf c0s x)) 1000)")
  will return an object representing that same plot that will draw it
  if `print`ed.  The collected dataset can also be extracted from the
  object for more flexible custom plotting.

  The format specifications are inspired loosely by the classic
  printf.  To wit, each individual plot that appears on a page is
  specified by some line noise consisting of format characters
  matching the following regex

  [<geom>]*(<stream>?<scale>?){1,3}

  specifying
  - the geometric objects to draw the plot with
  - for each dimension (x, y, and color, respectively)
    - the data stream to use
    - the scale

  Each requested data stream is sampled once every time the inference
  program executes the plotf instruction, and the plot shows all of
  the samples after inference completes.

  The possible geometric objects are:
    _p_oint, _l_ine, _b_ar, and _h_istogram
  The possible data streams are:
    _<an integer>_ that expression, 0-indexed,
    _%_ the next expression after the last used one
    sweep _c_ounter, _t_ime (wall clock), log _s_core, and pa_r_ticle
  The possible scales are:
    _d_irect, _l_og

  TODO: Modifiers for how to treat multiple particles: distinguished
  (current implementation, good default), mean, median, all (what
  exactly would all mean?  2-D table? Splice and hope?)

  TODO: Modifiers for how to treat overplotting?  (Exactly identical
  discrete samples; continuous samples that are close enough for the
  points to overlap; control or good choice of point size?; 2D kernel
  density nonsense?)

  If one stream is indicated for a 2-D plot (points or lines), the x
  axis is filled in with the sweep counter.  If three streams are
  indicated, the third is mapped to color.

  If the given specification is a list, make all those plots at once.

  """
  def __init__(self, spec, names, exprs):
    from plot_spec import PlotSpec
    self.spec_string = spec
    self.spec = PlotSpec(spec)
    self.names = names
    self.exprs = exprs
    self.data = dict([(name, []) for name in names + ["sweeps", "time (s)", "log score", "particle"]])
    self.sweep = 0
    self.time = time.time() # For sweep timing, should it be requested
    self.next_index = 0

  def add_data_from(self, engine, index):
    values = engine.sample_all(self.exprs[index])
    self.data[self.names[index]].extend(values)
    self.next_index = index+1

  def add_data(self, engine):
    self.next_index = 0
    self.sweep += 1
    the_time = time.time() - self.time
    touched = set()
    for stream in self.spec.streams():
      if stream in touched:
        continue
      else:
        touched.add(stream)
      if stream == "c":
        self.data["sweeps"].extend([self.sweep] * len(engine.traces))
      elif stream == "r": # TODO Wanted "p" for "particle", but may conflict with "p" for "point"
        self.data["particle"].extend(range(len(engine.traces)))
      elif stream == "t":
        self.data["time (s)"].extend([the_time] * len(engine.traces))
      elif stream == "s":
        self.data["log score"].extend(engine.logscore_all())
      elif stream == "" or stream == "%":
        self.add_data_from(engine, self.next_index)
      else:
        self.add_data_from(engine, int(stream))

  def dataset(self):
    for name in ["sweeps", "time (s)", "log score", "particle"] + self.names:
      if len(self.data[name]) == 0:
        # Data source was not requested; remove it to avoid confusing pandas
        del self.data[name]
    from pandas import DataFrame
    from venture.ripl.utils import _strip_types_from_dict_values
    return DataFrame.from_dict(_strip_types_from_dict_values(self.data))

  def draw(self):
    return self.spec.draw(self.dataset(), self.names)

  def plot(self):
    self.spec.plot(self.dataset(), self.names)

  def __str__(self):
    "Not really a string method, but does get itself displayed when printed."
    self.plot()
    return "a plot"
