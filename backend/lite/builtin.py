# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

# Importing for re-export pylint:disable=unused-import
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.sp_registry import builtInSPs
from venture.lite.sp_registry import builtInSPsIter
import venture.lite.value as v

# These modules actually define the PSPs.
# Import them for their effect on the registry.
# pylint:disable=unused-import
import venture.lite.venmath
import venture.lite.basic_sps
import venture.lite.vectors
import venture.lite.records
import venture.lite.functional
import venture.lite.conditionals
import venture.lite.csp
import venture.lite.eval_sps
import venture.lite.msp
import venture.lite.scope
import venture.lite.discrete
import venture.lite.continuous
import venture.lite.dirichlet
import venture.lite.crp
import venture.lite.hmm
import venture.lite.cmvn
import venture.lite.function
import venture.lite.gp
import venture.untraced.usp

# The types in the types module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False),
           "nil" : v.VentureNil() }
