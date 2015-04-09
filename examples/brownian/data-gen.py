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

def main():
  step = float(sys.argv[1])
  noise = float(sys.argv[2])
  r = s.Puma().make_church_prime_ripl()
  r.execute_program(build_brownian_model(step, noise))
  for i in range(8):
    print i, r.sample("(obs_fun %s)" % i)

if __name__ == "__main__":
  main()
