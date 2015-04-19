# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

import sys

import venture.shortcuts as s
from model import build_brownian_model
import measurement_plugin as measure

def main():
  r = s.Lite().make_church_prime_ripl()
  measure.set_answer(1)
  measure.__venture_start__(r)
  r.infer("(resample 6)")
  r.execute_program(build_brownian_model("(gamma 1 1)", "(gamma 1 1)"))
  r.infer("(call_back collect brown_step)")
  for (pos, val) in [(0, -0.150939311411),
                     (1, 0.592875979596),
                     (2, 0.463152378987),
                     (3, 1.01715231231),
                     (4, 0.125545541802),
                     (5, -0.526779818693),
                     (6, -1.12678765665),
                     (7, -1.58748636726)]:
    r.execute_program("""
[observe (obs_fun %s) %s]
[infer (resample 6)]
[infer (nesterov exp all 0.01 5 1)]
[infer (call_back collect brown_step)]""" % (pos, val))
  r.infer("(call_back emit)")

if __name__ == "__main__":
  main()
