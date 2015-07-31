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

from sp_registry import registerBuiltinSP, builtInSPs, builtInSPsIter # Importing for re-export pylint:disable=unused-import

import value as v
import types as t
from utils import raise_
from exception import VentureValueError

from sp_help import *

# These modules actually define the PSPs.
import venmath
import basic_sps
import vectors
import functional
import conditionals
import csp
import eval_sps
import msp
import scope
import discrete
import continuous
import dirichlet
import crp
import hmm
import cmvn
import function
import gp

# The types in the types module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def debug_print(label, value):
  print 'debug ' + label + ': ' + str(value)
  return value

registerBuiltinSP("debug",
                  deterministic_typed(debug_print, [t.SymbolType(), t.AnyType("k")], t.AnyType("k"),
                                      descr = "Print the given value, labeled by a Symbol. Return the value. Intended for debugging or for monitoring execution."))


registerBuiltinSP("zip", deterministic_typed(zip, [t.ListType()], t.HomogeneousListType(t.ListType()), variadic=True,
                                             descr="zip returns a list of lists, where the i-th nested list contains the i-th element from each of the input arguments"))

registerBuiltinSP("value_error", deterministic_typed(lambda s: raise_(VentureValueError(str(s))),
                                                     [t.AnyType()], t.AnyType()))
