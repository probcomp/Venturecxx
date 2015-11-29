from venture.lite.trace import *
from venture.lite.regen import *
from venture.lite.detach import *
from sp import *
from venture.lite.discrete import *

def evalFamily(trace, address, exp, env, constraint=None):
    if e.isVariable(exp):
        try:
            sourceNode = env.findSymbol(exp)
        except VentureError as err:
            import sys
            info = sys.exc_info()
            raise VentureException("evaluation", err.message, address=address), None, info[2]
        assert constraint is None, "Cannot constrain" # TODO does it make sense to evaluate a variable lookup subject to a constraint? does this turn the below regen into an absorb? what if multiple lookups of the same variable are constrained to different values? can we detect this as a case of source having already been regenned?
        weight = 0 # TODO regen source node?
        return (weight, trace.createLookupNode(address, sourceNode))
    elif e.isSelfEvaluating(exp):
        assert constraint is None, "Cannot constrain"
        return (0, trace.createConstantNode(address,exp))
    elif e.isQuotation(exp): return (0, trace.createConstantNode(address,e.textOfQuotation(exp)))
    else: # SP application
        weight = 0
        nodes = []
        for index, subexp in enumerate(exp):
            addr = address.extend(index)
            w, n = evalFamily(trace, addr, subexp, env)
            weight += w
            nodes.append(n)

        outputNode = trace.createApplicationNode(address, nodes[0], nodes[1:], env)
        try:
            weight += apply(trace, outputNode, constraint)
        except VentureException:
            raise # Avoid rewrapping with the below
        except Exception as err:
            import sys
            info = sys.exc_info()
            raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
        assert isinstance(weight, numbers.Number)
        return (weight, outputNode)

def apply(trace, node, constraint):
    sp = trace.spAt(node)
    args = trace.argsAt(node)
    newValue, weight = sp.apply(args, constraint)
    trace.setValueAt(node, newValue)
    return weight

def unapply(trace, node, constraint):
    sp = trace.spAt(node)
    args = trace.argsAt(node)
    oldValue = trace.valueAt(node)
    weight = sp.unapply(oldValue, args, constraint)
    trace.setValueAt(node, None)
    return weight

def constrain(trace, node, constraint):
    sp = trace.spAt(node)
    args = trace.argsAt(node)
    oldValue = trace.valueAt(node)
    sp.unapply(oldValue, args, None)
    newValue, weight = sp.apply(args, constraint)
    trace.setValueAt(node, newValue)
    return weight

def unevalFamily(trace, node, constraint=None):
    weight = 0
    if isConstantNode(node): pass
    elif isLookupNode(node):
        assert len(trace.parentsAt(node)) == 1
        trace.disconnectLookup(node)
        trace.setValueAt(node,None)
        # todo detach source node
    else:
        assert isOutputNode(node)
        weight += unapply(trace, node, constraint)
        for operandNode in reversed(node.operandNodes):
            weight += unevalFamily(trace, operandNode)
        weight += unevalFamily(trace, node.operatorNode)
    return weight

LiteTrace = Trace
class Trace(LiteTrace):
    def __init__(self):
        self.globalEnv = VentureEnvironment()
        self.families = {}
        self.unpropagatedObservations = {}

        self.bindPrimitiveSP('beta', SimpleRandomSPWrapper(builtInSPs()['beta'].outputPSP))
        self.bindPrimitiveSP('flip', SimpleRandomSPWrapper(builtInSPs()['flip'].outputPSP))
        self.bindPrimitiveSP('add', SimpleDeterministicSPWrapper(builtInSPs()['add'].outputPSP))
        coin = SimpleRandomSPWrapper(
            TypedPSP(CBetaBernoulliOutputPSP(1.0, 1.0),
                     SPType([], t.BoolType())))
        coin.constructSPAux = BetaBernoulliSPAux
        self.bindPrimitiveSP('coin', coin)

    def extractValue(self, id):
        return self.boxValue(self.extractRaw(id))

    def extractRaw(self,id): return self.valueAt(self.families[id])

    def eval(self, id, exp):
        assert id not in self.families
        (_, family) = evalFamily(self, Address(List(id)), self.unboxExpression(exp), self.globalEnv)
        self.families[id] = family

    def uneval(self, id):
        assert id in self.families
        unevalFamily(self, self.families[id])
        del self.families[id]

    def bindInGlobalEnv(self, sym, id):
        try:
            self.globalEnv.addBinding(sym,self.families[id])
        except VentureError as e:
            raise VentureException("invalid_argument", message=e.message, argument="symbol")

    def observe(self, id, val):
        node = self.families[id]
        self.unpropagatedObservations[node] = self.unboxValue(val)

    def makeConsistent(self):
        weight = 0
        for node, val in self.unpropagatedObservations.iteritems():
            # TODO do this with regen to deal with propagation and references and stuff
            appNode = self.getConstrainableNode(node)
            node.observe(val)
            weight += constrain(self, appNode, node.observedValue)
        self.unpropagatedObservations.clear()
        return weight

    def unobserve(self, id):
        print 'unobserve', id

    def select(self, scope, block):
        print 'select', scope, block
        return None

    def just_detach(self, scaffold):
        print 'detach', scaffold
        return 0, None

    def just_regen(self, scaffold):
        print 'regen', scaffold
        return 0

    def just_restore(self, scaffold, rhoDB):
        print 'restore', scaffold, rhoDB
        return 0

    # modified from lite trace due to no more request node
    def createApplicationNode(self,address,operatorNode,operandNodes,env):
        outputNode = OutputNode(address,operatorNode,operandNodes,None,env)
        self.addChildAt(operatorNode,outputNode)
        for operandNode in operandNodes:
            self.addChildAt(operandNode,outputNode)
        return outputNode
