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
    elif spec == self.plot.spec and names == self.plot.names and exprs == self.plot.exprs:
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
  def __init__(self, spec, names, exprs):
    self.spec = spec
    self.names = names
    self.exprs = exprs
    self.data = dict([(name, []) for name in names])
  def add_data(self, engine):
    for name, exp in zip(self.names, self.exprs):
      value = engine.sample(exp)
      self.data[name].append(value)
