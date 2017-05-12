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

import sys
import math

from venture.lite.exception import VentureBuiltinLKernelMethodError
from venture.lite.value import VentureValue
from venture.lite.utils import ensure_python_float

class LKernel(object):
  """A local proposal distribution for one node."""

  def forwardSimulate(self, _trace, _oldValue, _args):
    """Compute a proposed new value.

    In general, the proposal may depend on the old value (delta
    kernels).

    """
    raise VentureBuiltinLKernelMethodError("Cannot simulate %s", type(self))

  def forwardWeight(self, _trace, _newValue, _oldValue, _args):
    """The M-H acceptance term regen should include for this local proposal.

    For general kernels that depend on the former value ("delta
    kernels"), this should be the full M-H term

      Prior(newValue) Kernel(oldValue|newValue)
      -----------------------------------------
      Prior(oldValue) Kernel(newValue|oldValue)

    and the reverseWeight should be 0 (since the reverse probability
    cannot be computed before the new value is available in this
    case).

    Note that the likelihood is accounted for by later recursive calls
    to regen.

    """
    raise VentureBuiltinLKernelMethodError("Cannot compute forward weight of %s", type(self))

  def reverseWeight(self, _trace, _oldValue, _args):
    """The M-H acceptance term detach should include for this local proposal.

    For general kernels that depend on the former value, the reverse
    probability cannot be computed until a new value is simulated, and
    this method should return 0.  This method exists to interface with
    simulation kernels, that _can_ profitably compute the reverse
    weight without access to the value that will be proposed.

    """
    raise VentureBuiltinLKernelMethodError("Cannot compute reverse weight of %s", type(self))

class SimulationLKernel(LKernel):
  """A local proposal distribution that does not depend on the previous value of the node."""

  def forwardSimulate(self, trace, _oldValue, args):
    """Forward simulation must ignore the old value.

    Do not override this; define the "simulate" method instead."""
    return self.simulate(trace, args)

  def simulate(self, _trace, _args):
    """Compute a proposed new value, independently of the old one."""
    raise VentureBuiltinLKernelMethodError("Cannot simulate %s", type(self))

  def forwardWeight(self, trace, newValue, _oldValue, args):
    """The forward weight must ignore the old value.

    Do not override this; define the "weight" method instead."""
    return self.weight(trace, newValue, args)

  def weight(self, _trace, _value, _args):
    r"""Return the importance weight of this proposed value against the prior.

    In the case of simulation kernels, the M-H ratio factors as

    / Kernel(newValue) \   / Prior(oldValue)  \
    | ---------------- | * | ---------------- |
    \ Prior(newValue)  /   \ Kernel(oldValue) /

    and it is advantageous to compute the two terms separately.  The
    "weight" method of a SimulationLKernel should return such a term
    for the given value.

    """
    raise VentureBuiltinLKernelMethodError("Cannot compute the weight of %s", type(self))

  def reverseWeight(self, trace, oldValue, args):
    """The reverse weight can be computed without knowing the new value.

    Do not override this; define the "weight" method instead."""
    return self.weight(trace, oldValue, args)

  def gradientOfReverseWeight(self, _trace, _value, args):
    """The gradient of the reverse weight, with respect to the old value and the arguments."""
    return (0, [0 for _ in args.operandNodes])

  def weightBound(self, _trace, _value, _args):
    """An upper bound on the value of weight over the variation
    possible by changing the values of everything in the arguments
    whose value is None.  Useful for rejection sampling."""
    raise VentureBuiltinLKernelMethodError("Cannot rejection auto-bound with weight-unbounded LKernel of type %s" % type(self))

class DeltaLKernel(LKernel):
  def reverseWeight(self, _trace, _oldValue, _args): return 0

class AAALKernel(LKernel):
  """An AAA LKernel differs from an LKernel only in the weight contract.

  To wit, the weight of an AAA LKernel is expected to include the
  relevant terms from the full joint density on the node, not just the
  prior.  The likelihood should be computable from the statistics that
  the made SP maintains.

  """
  pass

class SimulationAAALKernel(SimulationLKernel, AAALKernel):
  """An AAA LKernel that is also a simulation kernel."""

class PosteriorAAALKernel(SimulationAAALKernel):
  """An AAA LKernel that proposes exactly from the local posterior.

  In this case, the weight is the joint density divided by the
  posterior, which is the marginal likelihood of the data.

  """

  def __init__(self,makerPSP): self.makerPSP = makerPSP
  def weight(self, _trace, _newValue, args):
    return self.makerPSP.marginalLogDensityOfData(args.madeSPAux(), args)
  def gradientOfReverseWeight(self, _trace, _value, args):
    """The gradient of the reverse weight, with respect to the value and the arguments."""
    return (0, self.makerPSP.gradientOfLogDensityOfData(args.madeSPAux(), args))
  def weightBound(self, _trace, _value, args):
    # Going through the maker here because the new value is liable to
    # be None when computing bounds for rejection, but the maker
    # should know enough about its possible values future to answer my
    # question.
    return self.makerPSP.madeSpLogDensityOfDataBound(args.madeSPAux())

class DeterministicMakerAAALKernel(PosteriorAAALKernel):
  """If the maker is deterministic, then the proposal is necessarily the
  same as the prior (which is also the posterior), and the AAA LKernel
  weight is the likelihood.

  """
  def simulate(self, _trace, args):
    spRecord = self.makerPSP.simulate(args)
    spRecord.spAux = args.madeSPAux()
    return spRecord
  def weight(self, _trace, newValue, args):
    from venture.lite.sp import VentureSPRecord
    assert isinstance(newValue,VentureSPRecord)
    return newValue.sp.outputPSP.logDensityOfData(args.madeSPAux())

class DeterministicLKernel(SimulationLKernel):
  def __init__(self,psp,value):
    self.psp = psp
    self.value = value
    assert isinstance(value, VentureValue)

  def simulate(self, _trace, _args):
    return self.value

  def weight(self, _trace, newValue, args):
    answer = self.psp.logDensity(newValue,args)
    return ensure_python_float(answer)

  def gradientOfReverseWeight(self, _trace, value, args):
    return self.psp.gradientOfLogDensity(value, args)

######## Variational #########

class VariationalLKernel(SimulationLKernel):
  def gradientOfLogDensity(self, _value, _args): return 0
  def updateParameters(self,gradient,gain,stepSize): pass

class DefaultVariationalLKernel(VariationalLKernel):
  def __init__(self,psp,args):
    self.psp = psp
    self.parameters = args.operandValues()
    self.parameterScopes = psp.getParameterScopes()

  def simulate(self, _trace, args):
    return self.psp.simulateNumeric(self.parameters, args.np_prng())

  def weight(self, _trace, newValue, args):
    ld = self.psp.logDensityNumeric(newValue,args.operandValues())
    proposalLD = self.psp.logDensityNumeric(newValue,self.parameters)
    w = ld - proposalLD
    assert not math.isinf(w) and not math.isnan(w)
    return w

  def gradientOfLogDensity(self, value, args):
    from venture.lite.sp_use import ReplacingArgs
    new_args = ReplacingArgs(args, self.parameters)
    # Ignore the derivative of the value because we do not care about it
    (_, grad) = self.psp.gradientOfLogDensity(value, new_args)
    return grad

  def updateParameters(self,gradient,gain,stepSize):
    # TODO hacky numerical stuff
    minFloat = -sys.float_info.max
    maxFloat = sys.float_info.max
    for i in range(len(self.parameters)):
      self.parameters[i] += gradient[i] * gain * stepSize
      if self.parameters[i] < minFloat: self.parameters[i] = minFloat
      if self.parameters[i] > maxFloat: self.parameters[i] = maxFloat
      if self.parameterScopes[i] == "POSITIVE_REAL" and \
         self.parameters[i] < 0.1: self.parameters[i] = 0.1
      assert not math.isinf(self.parameters[i]) and not math.isnan(self.parameters[i])
