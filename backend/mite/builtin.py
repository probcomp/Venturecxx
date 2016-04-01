import venture.lite.value as v

# Importing for re-export pylint:disable=unused-import
from venture.mite.sp_registry import builtInSPs

# These modules actually define the SPs.
# Import them for their effect on the registry.
# pylint:disable=unused-import
import venture.mite.sps.lite_sp

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False),
           "nil" : v.VentureNil() }
