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

from collections import OrderedDict
import random

import numpy.random as npr

from venture.lite.request import Request
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_use import MockArgs
from venture.lite.value import VentureValue

# Part of a mechanism for allowing Lite SPs to be called from
# Puma. The ForeignLiteSP class is a wrapper that handles value
# translation from Lite VentureValues to stack dicts, which can be
# consumed by another backend (as in new_cxx/inc/sps/lite.h).

def fromStackDict(thing):
    # proxy for VentureValue.fromStackDict that handles SPs by unwrapping them
    # TODO: should foreign_sp be a recognized stack dict type?
    # should this become the normal stack representation for SPs?
    if thing is None:
        return None
    elif thing["type"] == "foreign_sp":
        return VentureSPRecord(thing["sp"].sp, thing["aux"])
    elif thing["type"] == "request":
        return Request(thing["value"]["esrs"], thing["value"]["lsrs"])
    else:
        return VentureValue.fromStackDict(thing)

def asStackDict(thing):
    # proxy for VentureValue.asStackDict that handles SPs by wrapping them
    if isinstance(thing, VentureSPRecord):
        return OrderedDict([
            ("type", "foreign_sp"),
            ("value", thing.show()),
            ("sp", ForeignLiteSP(thing.sp)),
            ("aux", thing.spAux),
        ])
    elif isinstance(thing, Request):
        return OrderedDict([
            ("type", "request"),
            ("value",
             OrderedDict([("esrs", thing.esrs), ("lsrs", thing.lsrs)])),
        ])
    else:
        return thing.asStackDict()

def asArgsObject(args):
    seed = args['seed']
    assert seed is not None
    prng = random.Random(seed)
    return MockArgs(
        map(fromStackDict, args.get('operandValues')),
        args.get('spaux'),
        py_rng=random.Random(prng.randint(1, 2**31 - 1)),
        np_rng=npr.RandomState(prng.randint(1, 2**31 - 1)),
        madeSPAux=args.get('madeSPAux'))

class ForeignLitePSP(object):
    """A wrapper around a Lite PSP that can be called by other backends."""

    def __init__(self, psp):
        self.psp = psp

    def simulate(self, args):
        args = asArgsObject(args)
        result = self.psp.simulate(args)
        return asStackDict(result)

    def logDensity(self, value, args):
        value = fromStackDict(value)
        args = asArgsObject(args)
        result = self.psp.logDensity(value, args)
        return result

    def incorporate(self, value, args):
        value = fromStackDict(value)
        args = asArgsObject(args)
        self.psp.incorporate(value, args)

    def unincorporate(self, value, args):
        value = fromStackDict(value)
        args = asArgsObject(args)
        self.psp.unincorporate(value, args)

    def logDensityOfData(self, aux):
        return self.psp.logDensityOfData(aux)

    def isRandom(self):
        return self.psp.isRandom()

    def canAbsorb(self):
        try:
            # try stubbing the node information...
            return self.psp.canAbsorb(None, None, None)
        except AttributeError:
            import warnings
            warnings.warn("Non-trivial canAbsorb methods not supported in foreign procedures")
            return False

    def childrenCanAAA(self):
        return self.psp.childrenCanAAA()

    def getAAALKernel(self):
        return ForeignLiteLKernel(self.psp.getAAALKernel())

    def canEnumerate(self):
        return self.psp.canEnumerate()

    def enumerateValues(self, args):
        args = asArgsObject(args)
        result = self.psp.enumerateValues(args)
        return [asStackDict(value) for value in result]

class ForeignLiteLKernel(object):
    # TODO This is not actually an LKernel, because its methods do not
    # accept the trace argument (since it is not effectively transferred)
    def __init__(self, lkernel):
        self.lkernel = lkernel

    def forwardSimulate(self, oldValue, args):
        oldValue = fromStackDict(oldValue)
        args = asArgsObject(args)
        # stub the trace
        # TODO: do any lkernels actually use the trace argument?
        result = self.lkernel.forwardSimulate(None, oldValue, args)
        return asStackDict(result)

    def forwardWeight(self, newValue, oldValue, args):
        newValue = fromStackDict(newValue)
        oldValue = fromStackDict(oldValue)
        args = asArgsObject(args)
        # stub the trace
        # TODO: do any lkernels actually use the trace argument?
        result = self.lkernel.forwardWeight(None, newValue, oldValue, args)
        return result

    def reverseWeight(self, oldValue, args):
        oldValue = fromStackDict(oldValue)
        args = asArgsObject(args)
        # stub the trace
        # TODO: do any lkernels actually use the trace argument?
        result = self.lkernel.reverseWeight(None, oldValue, args)
        return result

class ForeignLiteSP(object):
    """A wrapper around a Lite SP that can be called by other backends."""

    def __init__(self, sp):
        self.requestPSP = ForeignLitePSP(sp.requestPSP)
        self.outputPSP = ForeignLitePSP(sp.outputPSP)
        self.sp = sp

    def constructSPAux(self):
        return self.sp.constructSPAux()

    def constructLatentDB(self):
        return self.sp.constructLatentDB()
    def simulateLatents(self, args, lsr, shouldRestore, latentDB):
        return self.sp.simulateLatents(asArgsObject(args), lsr,
                                       shouldRestore, latentDB)
    def detachLatents(self, args, lsr, latentDB):
        return self.sp.detachLatents(asArgsObject(args), lsr, latentDB)

    def hasAEKernel(self):
        return self.sp.hasAEKernel()
    def AEInfer(self, aux, seed):
        assert seed is not None
        np_rng = npr.RandomState(seed)
        return self.sp.AEInfer(aux, np_rng)

    def show(self, spaux):
        return self.sp.show(spaux)
