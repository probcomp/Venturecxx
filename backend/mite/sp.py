from __future__ import print_function

from venture.lite.request import Request, ESR
from venture.lite.address import emptyAddress

class StochasticProcedure(object):
    def apply(self, args, constraint):
        raise NotImplementedError

    def unapply(self, value, args, constraint):
        raise NotImplementedError

    def simulate(self, args):
        raise NotImplementedError

    def logp(self, value, args):
        raise NotImplementedError

    def incorporate(self, value, args):
        pass

    def unincorporate(self, value, args):
        pass

    def request(self, args):
        raise NotImplementedError

    # for backward compatibility with existing implementation
    def constructSPAux(self): return None
    def hasAEKernel(self): return False
    def show(self, _spaux): return '<SP>'

class SimpleRandomSP(StochasticProcedure):
    def apply(self, args, constraint):
        if constraint is not None:
            value = constraint
            weight = self.logp(value, args)
        else:
            value = self.simulate(args)
            weight = 0.
        self.incorporate(value, args)
        return value, weight

    def unapply(self, value, args, constraint):
        self.unincorporate(value, args)
        if constraint is not None:
            weight = -self.logp(value, args)
        else:
            weight = 0.
        return weight

class SimpleLikelihoodFreeSP(StochasticProcedure):
    def apply(self, args, constraint):
        assert constraint is None
        value = self.simulate(args)
        weight = 0.
        self.incorporate(value, args)
        return value, weight

    def unapply(self, value, args, constraint):
        assert constraint is None
        self.unincorporate(value, args)
        weight = 0.
        return weight

LiteESR = ESR
class ESR(LiteESR):
    def __init__(self, id, exp, addr, env, constraint=None):
        self.id = id
        self.exp = exp
        self.addr = addr
        self.env = env
        self.constraint = constraint

class ESRPtr(LiteESR):
    def __init__(self, id, constraint=None):
        self.id = id
        self.constraint = constraint

class SimpleRequestingSP(StochasticProcedure):
    def apply(self, args, constraint):
        id = self.requestId(args)
        exp, env = self.requestEval(args)
        request = Request([ESR(id, exp, emptyAddress, env, constraint)])
        [value], weight = args.requestValues(request)
        return value, weight

    def unapply(self, value, args, constraint):
        id = self.requestId(args)
        request = Request([ESRPtr(id, constraint)])
        weight = args.requestFree(request)
        return weight

class SimpleArgsWrapper(object):
    def __init__(self, operandValues, spaux=None, ripl=None, requesters=None):
        self._operandValues = operandValues
        self._spaux = spaux
        self._ripl = ripl
        self._requesters = requesters
        self.env = None

    def operandValues(self):
        return self._operandValues

    def spaux(self):
        return self._spaux

    def _evalESR(self, esr):
        # temporary hack: use an embedded Lite ripl.
        did = 'esr' + hex(hash(esr.id))
        assert esr.env is None
        self._ripl.assume(did, esr.exp, did)
        if esr.constraint is not None:
            self._ripl.infer(['set_particle_log_weights', ['array', 0]])
            self._ripl.observe(did, esr.constraint, 'oid')
            [weight] = self._ripl.infer(['particle_log_weights'])
            self._ripl.forget('oid')
        else:
            weight = 0
        self._requesters[esr.id].add(id(self))
        return weight

    def _unevalESR(self, esr):
        did = 'esr' + hex(hash(esr.id))
        if esr.constraint is not None:
            self._ripl.infer(['set_particle_log_weights', ['array', 0]])
            self._ripl.observe(did, esr.constraint, 'oid')
            [weight] = self._ripl.infer(['particle_log_weights'])
            self._ripl.forget('oid')
        else:
            weight = 0
        self._ripl.forget(did)
        return weight

    def requestValues(self, request):
        values = []
        weight = 0
        for esr in request.esrs:
            if esr.id not in self._requesters:
                self._requesters[esr.id] = set()
                weight += self._evalESR(esr)
            # temporary hack: get the value from the embedded ripl
            did = 'esr' + hex(hash(esr.id))
            values.append(self._ripl.report(did))
        # TODO lsrs
        return values, weight

    def requestFree(self, request):
        weight = 0
        for esr in request.esrs:
            self._requesters[esr.id].remove(id(self))
            if not self._requesters[esr.id]:
                del self._requesters[esr.id]
                weight += self._unevalESR(esr)
        return weight

class SimpleSPWrapper(StochasticProcedure):
    def __init__(self, outputPSP):
        self.outputPSP = outputPSP

    def simulate(self, args):
        return self.outputPSP.simulate(args)

    def logp(self, value, args):
        return self.outputPSP.logDensity(value, args)

    def incorporate(self, value, args):
        return self.outputPSP.incorporate(value, args)

    def unincorporate(self, value, args):
        return self.outputPSP.unincorporate(value, args)

class SimpleRandomSPWrapper(SimpleSPWrapper, SimpleRandomSP):
    pass

class SimpleDeterministicSPWrapper(SimpleSPWrapper, SimpleLikelihoodFreeSP):
    pass

class RequestFlipSP(SimpleRequestingSP):
    def requestId(self, args):
        return id(args)

    def requestEval(self, args):
        exp = ['flip'] + args.operandValues()
        env = args.env
        return exp, env


def test():
    from venture.lite.discrete import CBetaBernoulliOutputPSP, BetaBernoulliSPAux
    from venture.lite.continuous import NormalOutputPSP
    from venture.lite.sp_help import deterministic_psp
    from venture.shortcuts import make_lite_church_prime_ripl

    normal = SimpleRandomSPWrapper(NormalOutputPSP())

    args = SimpleArgsWrapper([10, 1])
    print(normal.apply(args, None))
    print(normal.apply(args, None))
    print(normal.apply(args, 11))
    print(normal.apply(args, 12))
    print(normal.apply(args, 13))
    print(normal.apply(args, 9))
    print(normal.apply(args, 8))
    print(normal.apply(args, 7))

    coin = SimpleRandomSPWrapper(CBetaBernoulliOutputPSP(1.0, 1.0))
    bbaux = BetaBernoulliSPAux()
    args = SimpleArgsWrapper([], bbaux)
    print(coin.apply(args, False))
    print(coin.apply(args, False))
    print(coin.apply(args, True))
    print(coin.apply(args, True))
    (x, w) = coin.apply(args, None)
    print((x, w))
    print(coin.unapply(False, args, False))
    print(coin.unapply(False, args, False))
    print(coin.unapply(True, args, True))
    print(coin.unapply(True, args, True))
    print(coin.unapply(x, args, None))

    plus = SimpleDeterministicSPWrapper(deterministic_psp(lambda x, y: x + y))

    print(plus.apply(SimpleArgsWrapper([1, 2]), None))
    print(plus.apply(SimpleArgsWrapper([3, 4]), None))
    print(plus.unapply(3, SimpleArgsWrapper([1, 2]), None))
    print(plus.unapply(7, SimpleArgsWrapper([3, 4]), None))
    try:
        plus.apply([2,2], 5)
    except AssertionError:
        pass
    else:
        assert False

    flip = RequestFlipSP()
    requesters = {}
    ripl = make_lite_church_prime_ripl()
    args1 = SimpleArgsWrapper([0.7], ripl=ripl, requesters=requesters)
    args2 = SimpleArgsWrapper([0.7], ripl=ripl, requesters=requesters)
    args3 = SimpleArgsWrapper([0.7], ripl=ripl, requesters=requesters)
    args4 = SimpleArgsWrapper([0.7], ripl=ripl, requesters=requesters)
    (x1, w1) = flip.apply(args1, None)
    (x2, w2) = flip.apply(args2, None)
    (x3, w3) = flip.apply(args3, None)
    (x4, w4) = flip.apply(args4, None)
    print((x1, w1))
    print((x2, w2))
    print((x3, w3))
    print((x4, w4))
    print(flip.unapply(x1, args1, x1))
    print(flip.apply(args1, x1))
    print(flip.unapply(x2, args2, x2))
    print(flip.apply(args2, x2))
    print(flip.unapply(x3, args3, x3))
    print(flip.unapply(x4, args4, x4))
    print(flip.apply(args3, x3))
    print(flip.apply(args4, x4))

if __name__ == '__main__':
    test()
