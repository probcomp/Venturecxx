import venture.lite.value as v

# Importing for re-export pylint:disable=unused-import
from venture.mite.sp_registry import builtInSPs

# These modules actually define the SPs.
# Import them for their effect on the registry.
# pylint:disable=unused-import
import venture.mite.traces
import venture.mite.dep_graph
import venture.mite.sps.lite_sp
import venture.mite.sps.vs_simulation_sp
import venture.mite.sps.vs_full_sp
import venture.mite.sps.handle
import venture.mite.sps.proc
import venture.mite.sps.binomial_state
import venture.mite.sps.crp_state
import venture.mite.sps.mem_table
import venture.mite.sps.prelude

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False),
           "nil" : v.VentureNil() }
