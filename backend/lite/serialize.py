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

def topo_sort(trace, nodes):
    nodes = set(nodes)
    ret = []
    stack = []
    seen = set()
    for _, root in sorted(trace.families.items()):
        stack.append(root)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for parent in node.parents():
            stack.append(parent)
        if node in nodes:
            ret.append(node)
    assert len(ret) == len(nodes)
    return ret
