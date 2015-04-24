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

from venture.test.config import get_ripl, broken_in, on_inf_prim
import venture.value.dicts as v
from venture.ripl.utils import strip_types
from venture.lite.utils import logWeightsToNormalizedDirect

@broken_in("puma", "enumerative_diversify not implemented in Puma")
@on_inf_prim("enumerative_diversify")
def testEnumerativeSmoke():
  r = get_ripl()
  r.assume("x", "(categorical (simplex 0.1 0.2 0.3 0.4) (list 1 2 3 4))")
  r.infer("(enumerative_diversify default all)")
  assert np.allclose([1, 2, 3, 4], strip_types(r.sivm.core_sivm.engine.sample_all(v.sym("x"))))
  assert np.allclose([0.1, 0.2, 0.3, 0.4], logWeightsToNormalizedDirect(r.sivm.core_sivm.engine.model.log_weights))

@broken_in("puma", "enumerative_diversify not implemented in Puma")
@on_inf_prim("enumerative_diversify")
def testEnumerativeStacking():
  r = get_ripl()
  r.assume("x", "(categorical (simplex 0.1 0.2 0.3 0.4) (list 1 2 3 4))")
  r.infer("(enumerative_diversify default all)")
  r.infer("(enumerative_diversify default all)")
  assert np.allclose([1, 2, 3, 4] * 4, strip_types(r.sivm.core_sivm.engine.sample_all(v.sym("x"))))
  assert np.allclose([0.01, 0.02, 0.03, 0.04,
                      0.02, 0.04, 0.06, 0.08,
                      0.03, 0.06, 0.09, 0.12,
                      0.04, 0.08, 0.12, 0.16], #TODO Are these actually the weights I want here?
                     logWeightsToNormalizedDirect(r.sivm.core_sivm.engine.model.log_weights))
