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
from venture.engine import engine
from venture.lite import trace

class Engine(engine.Engine):

  def __init__(self, persistent_inference_trace=False):
    super(Engine, self).__init__(name="lite", Trace=trace.Trace, persistent_inference_trace=persistent_inference_trace)

  def ensure_rng_seeded_decently(self):
    # Do not frobnicate the random seed, because the Lite trace uses
    # Python's rng rather than seeding its own from the system clock.
    pass
