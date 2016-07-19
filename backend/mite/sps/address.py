"""Utilities for constructing addresses."""

import venture.lite.types as t

import venture.mite.address as addresses
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

# shell out to Python to evaluate an address expression
# TODO: add a real set of address combinators instead of this lazy hack
class PyAddressSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 1
    code = t.String.asPython(inputs[0])
    output = eval(code, vars(addresses))
    return t.Blob.asVentureValue(output)

registerBuiltinSP("pyaddress", PyAddressSP())
