from venture.lite.engine import Engine
from venture.lite.trace import Trace
from venture.lite.request import Request
from venture.lite.value import SPRef
from venture.lite.env import VentureEnvironment
from venture.lite.omegadb import OmegaDB
from venture.lite.scaffold import Scaffold, constructScaffold
from venture.lite.detach import detachAndExtract, unevalFamily
from venture.lite.regen import regenAndAttach, evalFamily, restore
from venture.lite.consistency import assertTrace, assertTorus

# dummy trace, for the convenience methods
trace = object.__new__(Trace)
pspAt = trace.pspAt
argsAt = trace.argsAt

class OrderedOmegaDB(OmegaDB):
    def __init__(self):
        super(OrderedOmegaDB, self).__init__()
        self.stack = []
    def hasValueFor(self, node):
        return True
    def getValue(self, node):
        if super(OrderedOmegaDB, self).hasValueFor(node):
            return super(OrderedOmegaDB, self).getValue(node)
        psp = pspAt(node)
        if psp.isRandom():
            value = self.stack.pop()
            if isinstance(value, (Request, SPRef, VentureEnvironment)):
                raise Exception("Cannot restore a randomly constructed %s" % type(value))
            return value
        else:
            # resimulate deterministic PSPs
            # TODO: is it better to store deterministic values or to resimulate?
            args = argsAt(node)
            return psp.simulate(args)
    def extractValue(self, node, value):
        super(OrderedOmegaDB, self).extractValue(node, value)
        psp = pspAt(node)
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

def ser_deser(engine):
    trace = engine.getDistinguishedTrace()
    scaffold = constructScaffold(trace, [trace.getAllNodesInScope('default')])
    assertTrace(trace, scaffold)

    _, omegaDB = detachAndExtract(trace, scaffold.border[0], scaffold, omegaDB = OrderedOmegaDB())
    assertTorus(scaffold)

    _ = regenAndAttach(trace, scaffold.border[0], scaffold, True, omegaDB, {})
    assertTrace(trace, scaffold)

    return engine

def ser_deser(engine):
    old_trace = engine.getDistinguishedTrace()
    directives = engine.directives
    directiveCounter = engine.directiveCounter

    engine = Engine()
    engine.directives = directives
    for did, directive in sorted(directives.items()):
        engine.directiveCounter = did - 1
        engine.replay(directive)
    engine.directiveCounter = directiveCounter
    new_trace = engine.getDistinguishedTrace()
    new_trace.makeConsistent()
    old_trace.makeConsistent()

    old_scaffold = constructScaffold(old_trace, [old_trace.getAllNodesInScope('default')])
    new_scaffold = constructScaffold(new_trace, [new_trace.getAllNodesInScope('default')])

    old_border = topo_sort(old_trace, old_scaffold.border[0])
    new_border = topo_sort(new_trace, new_scaffold.border[0])

    _, oldDB = detachAndExtract(old_trace, old_border, old_scaffold, omegaDB = OrderedOmegaDB())
    _, newDB = detachAndExtract(new_trace, new_border, new_scaffold)

    _ = regenAndAttach(old_trace, old_border, old_scaffold, True, oldDB, {})
    # _ = regenAndAttach(new_trace, new_border, new_scaffold, True, newDB, {})
    _ = regenAndAttach(new_trace, new_border, new_scaffold, True, oldDB, {})

    return engine

def ser_deser(engine):
    old_trace = engine.getDistinguishedTrace()
    directives = engine.directives
    directiveCounter = engine.directiveCounter

    old_trace.makeConsistent()
    omegaDB = OrderedOmegaDB()
    scaffold = Scaffold()

    for did, directive in sorted(directives.items(), reverse=True):
        if directive[0] == "observe":
            old_trace.unobserve(did)
            old_trace.families[did].isObservation = False
        unevalFamily(old_trace, old_trace.families[did], scaffold, omegaDB)

    for did, directive in sorted(directives.items()):
        restore(old_trace, old_trace.families[did], scaffold, omegaDB, {})
        if directive[0] == "observe":
            old_trace.observe(did, directive[2])

    engine = Engine()
    engine.directives = directives
    engine.directiveCounter = directiveCounter
    new_trace = engine.getDistinguishedTrace()

    def evalHelper(did, datum):
        exp = new_trace.unboxExpression(engine.desugarLambda(datum))
        _, new_trace.families[did] = evalFamily(new_trace, exp, new_trace.globalEnv, scaffold, True, omegaDB, {})

    for did, directive in sorted(directives.items()):
        if directive[0] == "assume":
            name, datum = directive[1], directive[2]
            evalHelper(did, datum)
            new_trace.bindInGlobalEnv(name, did)
        elif directive[0] == "observe":
            datum, val = directive[1], directive[2]
            evalHelper(did, datum)
            new_trace.observe(did, val)
        elif directive[0] == "predict":
            datum = directive[1]
            evalHelper(did, datum)

    return engine

def test_omegadb_serialize():
    from venture.shortcuts import make_lite_church_prime_ripl
    v = make_lite_church_prime_ripl()
    v.assume('tricky_prob', '(beta 1.0 1.0)')
    v.assume('coin_weight', '(mem (lambda (x) (if (flip tricky_prob) (beta 1.0 1.0) 0.5)))')
    v.assume('flip_coin', '(lambda (x) (flip (coin_weight x)))')
    # v.assume('coin', '(mem (lambda (x) (if (flip tricky_prob) (make_beta_bernoulli 1.0 1.0) flip)))')
    # v.assume('flip_coin', '(lambda (x) ((coin x)))')
    for i in range(5):
        v.observe('(flip_coin {})'.format(i), 'true')
    for i in range(10):
        v.predict('(flip_coin {})'.format(i), label='x{}'.format(i))
    v.infer(0)
    for i in range(10):
        print v.report('x{}'.format(i))
    v.sivm.core_sivm.engine = ser_deser(v.sivm.core_sivm.engine)
    for i in range(10):
        print v.report('x{}'.format(i))

if __name__ == '__main__':
    test_omegadb_serialize()
