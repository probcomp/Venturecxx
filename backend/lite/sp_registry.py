# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

"""The registry of Lite SPs."""

# You might be curious why a registry independent of the initial
# environment in the trace.  Several reasons:
# - There are multiple clients: Lite traces, Untraced traces, Vendoc
# - Trace construction involves additional activity (e.g., Venture SP
#   Records)

_builtInSPsList = []

def registerBuiltinSP(name, sp):
  _builtInSPsList.append([name, sp])

def builtInSPs():
  return dict(_builtInSPsList)

def builtInSPsIter():
  for item in _builtInSPsList:
    yield item
