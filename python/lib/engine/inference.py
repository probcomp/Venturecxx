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

  def infer(self, program):
    self.engine.incorporate()
    if 'command' in program and program['command'] == "resample":
      self.engine.resample(program['particles'])

    elif 'command' in program and program['command'] == "incorporate": pass

    elif program['kernel'] == "cycle":
      if 'subkernels' not in program:
        raise Exception("Cycle kernel must have things to cycle over (%r)" % program)
      for _ in range(program["transitions"]):
        for k in program["subkernels"]:
          self.infer(k)
    elif program["kernel"] == "mixture":
      for _ in range(program["transitions"]):
        self.infer(simulateCategorical(program["weights"], program["subkernels"]))
    else: # A primitive infer expression
      self.engine.primitive_infer(program)

