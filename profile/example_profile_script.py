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

from venture.shortcuts import *
import cProfile

def RIPL():
  return make_church_prime_ripl()

def loadTrickCoin():
  ripl = RIPL()
  ripl.assume("coin_is_tricky","(bernoulli 0.1)",label="istricky")
  ripl.assume("weight","(if coin_is_tricky (beta 1.0 1.0) 0.5)")
  ripl.observe("(bernoulli weight)","true")

  return ripl


def profileReferencesProgram(N):
  ripl = loadTrickCoin()
  cProfile.runctx("ripl.infer(%d)" % N,None,locals(),"profile_trickycoin.pyprof")

profileReferencesProgram(1000)

