from venture.lite.serialize_old import * ## backward compatibility

from venture.lite.omegadb import OmegaDB

class OrderedOmegaDB(OmegaDB):
    """OmegaDB that additionally maintains a stack, containing all stored
    values in insertion order. By analogy to OrderedDict.
    """

    def __init__(self, Trace):
        super(OrderedOmegaDB, self).__init__()
        self.stack = []

        # make a dummy trace to get the convenience methods
        trace = object.__new__(Trace)
        self.pspAt = trace.pspAt
        self.argsAt = trace.argsAt

    def hasValueFor(self, node):
        return True

    def getValue(self, node):
        # TODO: move these imports to the top level after fixing circular imports
        from venture.lite.request import Request
        from venture.lite.value import SPRef
        from venture.lite.env import VentureEnvironment

        if super(OrderedOmegaDB, self).hasValueFor(node):
            return super(OrderedOmegaDB, self).getValue(node)
        psp = self.pspAt(node)
        if psp.isRandom():
            value = self.stack.pop()
            if isinstance(value, (Request, SPRef, VentureEnvironment)):
                raise Exception("Cannot restore a randomly constructed %s" % type(value))
            return value
        else:
            # resimulate deterministic PSPs
            # TODO: is it better to store deterministic values or to resimulate?
            args = self.argsAt(node)
            return psp.simulate(args)

    def extractValue(self, node, value):
        # TODO: move these imports to the top level after fixing circular imports
        from venture.lite.request import Request
        from venture.lite.value import SPRef
        from venture.lite.env import VentureEnvironment

        super(OrderedOmegaDB, self).extractValue(node, value)
        psp = self.pspAt(node)
        if psp.isRandom():
            if isinstance(value, (Request, SPRef, VentureEnvironment)):
                raise Exception("Cannot restore a randomly constructed %s" % type(value))
            self.stack.append(value)

def dump_trace(trace, engine):
    ## TODO: move these imports to the top level
    from venture.lite.trace import Trace
    from venture.lite.scaffold import Scaffold
    from venture.lite.detach import unevalFamily
    from venture.lite.regen import restore

    directives = engine.directives

    omegaDB = OrderedOmegaDB(Trace)
    scaffold = Scaffold()

    for did, directive in sorted(directives.items(), reverse=True):
        if directive[0] == "observe":
            trace.unobserve(did)
            trace.families[did].isObservation = False
        unevalFamily(trace, trace.families[did], scaffold, omegaDB)

    for did, directive in sorted(directives.items()):
        restore(trace, trace.families[did], scaffold, omegaDB, {})
        if directive[0] == "observe":
            trace.observe(did, directive[2])

    return omegaDB.stack

def restore_trace(values, engine):
    ## TODO: move these imports to the top level
    from venture.lite.trace import Trace
    from venture.lite.scaffold import Scaffold
    from venture.lite.regen import evalFamily

    directives = engine.directives

    omegaDB = OrderedOmegaDB(Trace)
    omegaDB.stack = values
    scaffold = Scaffold()
    trace = Trace()

    def evalHelper(did, datum):
        exp = trace.unboxExpression(engine.desugarLambda(datum))
        _, trace.families[did] = evalFamily(trace, exp, trace.globalEnv, scaffold, True, omegaDB, {})

    for did, directive in sorted(directives.items()):
        if directive[0] == "assume":
            name, datum = directive[1], directive[2]
            evalHelper(did, datum)
            trace.bindInGlobalEnv(name, did)
        elif directive[0] == "observe":
            datum, val = directive[1], directive[2]
            evalHelper(did, datum)
            trace.observe(did, val)
        elif directive[0] == "predict":
            datum = directive[1]
            evalHelper(did, datum)

    return trace
