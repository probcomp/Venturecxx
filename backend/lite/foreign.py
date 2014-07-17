from value import VentureValue

# Part of a mechanism for allowing Lite SPs to be called from
# Puma. The ForeignLiteSP class is a wrapper that handles value
# translation from Lite VentureValues to stack dicts, which can be
# consumed by another backend (as in new_cxx/inc/sps/lite.h).

class ForeignArgs(object):
    """A mock Args object used to call a Lite SP from other backends."""

    def __init__(self, operandValues, output=True):
        self.node = None
        self.operandValues = operandValues
        self.operandNodes = [None for _ in self.operandValues]
        if output:
            self.requestValue = None
            self.esrValues = []
            self.esrNodes = []
            self.madeSPAux = None
            self.isOutput = True
        else:
            self.isOutput = False
        self.spaux = None
        self.env = None

class ForeignLiteSP(object):
    """A wrapper around a Lite SP that can be called by other backends."""

    def __init__(self, sp):
        self.sp = sp

    def simulateRequestPSP(self):
        # TODO: do something about requests
        return None

    def simulateOutputPSP(self, operandValues):
        operandValues = map(VentureValue.fromStackDict, operandValues)
        args = ForeignArgs(operandValues)
        result = self.sp.outputPSP.simulate(args)
        return result.asStackDict()

    def logDensityOutputPSP(self, value, operandValues):
        value = VentureValue.fromStackDict(value)
        operandValues = map(VentureValue.fromStackDict, operandValues)
        args = ForeignArgs(operandValues)
        result = self.sp.outputPSP.logDensity(value, args)
        return result
