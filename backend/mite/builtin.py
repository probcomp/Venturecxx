import venture.lite.value as v

# Importing for re-export pylint:disable=unused-import
from venture.mite.sp_registry import builtInSPs

# These modules actually define the SPs.
# Import them for their effect on the registry.
# pylint:disable=unused-import
import venture.mite.traces
import venture.mite.dep_graph
import venture.mite.sps.lite_sp
import venture.mite.sps.mem
import venture.mite.sps.dpmem
import venture.mite.sps.suff_stat_cat
import venture.mite.sps.trick_coin

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False),
           "nil" : v.VentureNil() }
