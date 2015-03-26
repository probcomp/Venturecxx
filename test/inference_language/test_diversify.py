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
  assert np.allclose([0.1, 0.2, 0.3, 0.4], logWeightsToNormalizedDirect(r.sivm.core_sivm.engine.log_weights))
