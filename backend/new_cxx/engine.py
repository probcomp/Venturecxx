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
import random

from venture.engine import engine
import libpumatrace as puma

import venture.lite.foreign as foreign

class Trace(object):
  def __init__(self, trace=None):
    if trace is None:
      self.trace = puma.Trace()
      # Poor Puma defaults its local RNG seed to the system time
      self.trace.set_seed(random.randint(1,2**31-1))
    else:
      assert isinstance(trace, puma.Trace)
      self.trace = trace

  def __getattr__(self, attrname):
    # Forward all other trace methods without modification
    return getattr(self.trace, attrname)

  def stop_and_copy(self):
    return Trace(self.trace.stop_and_copy())

  def short_circuit_copyable(self): return True

  # Not intercepting the "diversify" method because Puma doesn't
  # support it.  If Puma does come to support it, will need to wrap it
  # here to drop the copy_trace argument (because presumably Puma will
  # have no need of that, using stop_and_copy instead).

  def bindPrimitiveSP(self, name, sp):
    self.trace.bindPrimitiveSP(name, foreign.ForeignLiteSP(sp))

class Engine(engine.Engine):

  def __init__(self, persistent_inference_trace=False):
    super(Engine, self).__init__(name="puma", Trace=Trace, persistent_inference_trace=persistent_inference_trace)
