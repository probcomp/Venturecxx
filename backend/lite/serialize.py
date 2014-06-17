from venture.lite.serialize_old import * ## backward compatibility

from venture.lite.omegadb import OmegaDB

class OrderedOmegaDB(OmegaDB):
    """OmegaDB that additionally maintains a stack containing all stored
    values in insertion order. By analogy to OrderedDict.

    This uses the fact that the regen/eval order is deterministic and
    exactly the reverse of the detach/uneval order. Thus it can be
    used to detach one scaffold (producing a value stack), then regen
    into a different scaffold (consuming the value stack), provided
    they are equivalent.

    """

    def __init__(self, trace, values=None, boxed=False):
        super(OrderedOmegaDB, self).__init__()
        self.trace = trace
        self.stack = []
        if values is not None:
            if boxed:
                values = map(self.trace.unboxValue, values)
            self.stack.extend(values)

    def hasValueFor(self, node):
        return True

    def getValue(self, node):
        # TODO: move these imports to the top level after fixing circular imports
        from venture.lite.request import Request
        from venture.lite.value import SPRef
        from venture.lite.env import VentureEnvironment

        if super(OrderedOmegaDB, self).hasValueFor(node):
            return super(OrderedOmegaDB, self).getValue(node)

        psp = self.trace.pspAt(node)
        if psp.isRandom():
            value = self.stack.pop()
            if isinstance(value, (Request, SPRef, VentureEnvironment)):
                raise Exception("Cannot restore a randomly constructed %s" % type(value))
            return value
        else:
            # resimulate deterministic PSPs
            # TODO: is it better to store deterministic values or to resimulate?
            args = self.trace.argsAt(node)
            return psp.simulate(args)

    def extractValue(self, node, value):
        # TODO: move these imports to the top level after fixing circular imports
        from venture.lite.request import Request
        from venture.lite.value import SPRef
        from venture.lite.env import VentureEnvironment

        super(OrderedOmegaDB, self).extractValue(node, value)

        psp = self.trace.pspAt(node)
        if psp.isRandom():
            if isinstance(value, (Request, SPRef, VentureEnvironment)):
                raise Exception("Cannot restore a randomly constructed %s" % type(value))
            self.stack.append(value)

    def listValues(self, boxed=False):
        values = self.stack
        if boxed:
            values = map(self.trace.boxValue, values)
        return list(values)
