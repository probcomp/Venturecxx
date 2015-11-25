from venture.lite.trace import *
from venture.lite.regen import *
from venture.lite.detach import *

def evalFamily(trace, address, exp, env):
    if e.isVariable(exp):
        try:
            sourceNode = env.findSymbol(exp)
        except VentureError as err:
            import sys
            info = sys.exc_info()
            raise VentureException("evaluation", err.message, address=address), None, info[2]
        weight = 0 # todo regen source node?
        return (weight, trace.createLookupNode(address, sourceNode))
    elif e.isSelfEvaluating(exp): return (0, trace.createConstantNode(address,exp))
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
            weight += apply(trace, outputNode)
        except VentureException:
            raise # Avoid rewrapping with the below
        except Exception as err:
            import sys
            info = sys.exc_info()
            raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
        assert isinstance(weight, numbers.Number)
        return (weight, outputNode)

def unevalFamily(trace, node):
    weight = 0
    if isConstantNode(node): pass
    elif isLookupNode(node):
        assert len(trace.parentsAt(node)) == 1
        trace.disconnectLookup(node)
        trace.setValueAt(node,None)
        # todo detach source node
    else:
        assert isOutputNode(node)
        weight += unapply(trace, node)
        for operandNode in reversed(node.operandNodes):
            weight += unevalFamily(trace, operandNode)
        weight += unevalFamily(trace, node.operatorNode)
    return weight

LiteTrace = Trace
class Trace(LiteTrace):
    def __init__(self):
        self.globalEnv = VentureEnvironment()
        self.families = {}

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
        print 'observe', id, self.unboxValue(val)

    def makeConsistent(self):
        print 'makeConsistent'
        return 0

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
