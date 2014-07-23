from sp import VentureSP
from value import VentureValue

# Part of a mechanism for allowing Lite SPs to be called from
# Puma. The ForeignLiteSP class is a wrapper that handles value
# translation from Lite VentureValues to stack dicts, which can be
# consumed by another backend (as in new_cxx/inc/sps/lite.h).

def fromStackDict(thing):
    # proxy for VentureValue.fromStackDict that handles SPs by unwrapping them
    # TODO: should foreign_sp be a recognized stack dict type?
    # should this become the normal stack representation for SPs?
    if thing["type"] == "foreign_sp":
        return thing["sp"].sp
    else:
        return VentureValue.fromStackDict(thing)

def asStackDict(thing):
    # proxy for VentureValue.asStackDict that handles SPs by wrapping them
    if isinstance(thing, VentureSP):
        return {"type": "foreign_sp", "value": ForeignLiteSP(thing)}
    else:
        return thing.asStackDict()

class ForeignArgs(object):
    """A mock Args object used to call a Lite SP from other backends."""

    def __init__(self, args, output=True):
        self.node = None
        self.operandValues = map(fromStackDict, args.get('operandValues'))
        self.operandNodes = [None for _ in self.operandValues]
        if output:
            self.requestValue = None
            self.esrValues = []
            self.esrNodes = []
            self.madeSPAux = args.get('madeSPAux')
            self.isOutput = True
        else:
            self.isOutput = False
        self.spaux = args.get('spaux')
        self.env = None

class ForeignLitePSP(object):
    """A wrapper around a Lite PSP that can be called by other backends."""

    def __init__(self, psp):
        self.psp = psp

    def simulate(self, args):
        args = ForeignArgs(args)
        result = self.psp.simulate(args)
        return asStackDict(result)

    def logDensity(self, value, args):
        value = fromStackDict(value)
        args = ForeignArgs(args)
        result = self.psp.logDensity(value, args)
        return result

    def incorporate(self, value, args):
        value = fromStackDict(value)
        args = ForeignArgs(args)
        self.psp.incorporate(value, args)

    def unincorporate(self, value, args):
        value = fromStackDict(value)
        args = ForeignArgs(args)
        self.psp.unincorporate(value, args)

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

    def canEnumerate(self):
        return self.psp.canEnumerate()

    def enumerateValues(self, args):
        args = ForeignArgs(args)
        result = self.psp.enumerateValues(args)
        return [asStackDict(value) for value in result]

    def logDensityOfCounts(self, aux):
        return self.psp.logDensityOfCounts(aux)

class ForeignLiteSP(object):
    """A wrapper around a Lite SP that can be called by other backends."""

    def __init__(self, sp):
        # TODO: requestPSP (needs requests to be stackable)
        self.outputPSP = ForeignLitePSP(sp.outputPSP)
        self.sp = sp

    def constructSPAux(self):
        return self.sp.constructSPAux()

    def show(self, spaux):
        return self.sp.show(spaux)
