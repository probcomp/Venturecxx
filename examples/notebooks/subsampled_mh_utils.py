# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import numpy as np
from venture.lite.builtin import deterministic_typed
import venture.lite.types as t

def loadUtilSPs(ripl):
  utilSPsList = [
      [ "linear_logistic", deterministic_typed(lambda w,x: 1/(1+np.exp(-(w[0] + np.dot(w[1:], x)))),
          [t.HomogeneousArrayType(t.NumberType()), t.HomogeneousArrayType(t.NumberType())], t.NumberType(),
          descr="linear_logistic(w, x) returns the output of logistic regression with weight and input") ]]

  for name,sp in dict(utilSPsList).iteritems():
    ripl.bind_foreign_sp(name, sp)
