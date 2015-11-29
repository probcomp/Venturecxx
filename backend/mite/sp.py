from __future__ import print_function

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

class EvalRequest(object):
    def __init__(self, eid, exp, env):
        self.eid = eid
        self.exp = exp
        self.env = env

class SimpleRequestingSP(StochasticProcedure):
    def apply(self, args, constraint):
        eid = self.eid(args)
        exp, env = self.request(args)
        esr = EvalRequest(eid, exp, env)
        weight = args.makeRequest(esr, constraint)
        value = args.esrValue(eid)
        return value, weight

    def unapply(self, value, args, constraint):
        eid = self.eid(args)
        weight = args.unmakeRequest(eid, constraint)
        return weight

class SimpleArgsWrapper(object):
    def __init__(self, operandValues, spaux=None, ripl=None, requestCounts=None):
        self._operandValues = operandValues
        self._spaux = spaux
        self._ripl = ripl
        self._requestCounts = requestCounts

    def operandValues(self):
        return self._operandValues

    def spaux(self):
        return self._spaux

    def makeRequest(self, esr, constraint):
        if esr.eid in self._requestCounts:
            self._requestCounts[esr.eid][0] += 1
            return 0
        # temporary hack: use an embedded Lite ripl.
        did = 'esr' + hex(hash(esr.eid))
        assert esr.env is None
        self._ripl.assume(did, esr.exp, did)
        if constraint is not None:
            self._ripl.infer(['set_particle_log_weights', ['array', 0]])
            self._ripl.observe(did, constraint, 'oid')
            [weight] = self._ripl.infer(['particle_log_weights'])
            self._ripl.forget('oid')
        else:
            weight = 0
        self._requestCounts[esr.eid] = [1, 0]
        return weight

    def unmakeRequest(self, eid, constraint, collect=True):
        if collect:
            self._requestCounts[eid][0] -= 1
            if self._requestCounts[eid][0] > 0:
                return 0
            del self._requestCounts[eid]
            did = 'esr' + hex(hash(eid))
            if constraint is not None:
                self._ripl.infer(['set_particle_log_weights', ['array', 0]])
                self._ripl.observe(did, constraint, 'oid')
                [weight] = self._ripl.infer(['particle_log_weights'])
                self._ripl.forget('oid')
            else:
                weight = 0
            self._ripl.forget(did)
            return weight
        else:
            self._requestCounts[eid][1] += 1
            return 0

    def esrValue(self, eid):
        assert eid in self._requestCounts
        # temporary hack: get the value from the embedded ripl
        did = 'esr' + hex(hash(eid))
        return self._ripl.report(did)

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
    def eid(self, args):
        return id(args)

    def request(self, args):
        exp = ['flip'] + args.operandValues()
        env = None
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
    requestCounts = {}
    ripl = make_lite_church_prime_ripl()
    args1 = SimpleArgsWrapper([0.7], ripl=ripl, requestCounts=requestCounts)
    args2 = SimpleArgsWrapper([0.7], ripl=ripl, requestCounts=requestCounts)
    args3 = SimpleArgsWrapper([0.7], ripl=ripl, requestCounts=requestCounts)
    args4 = SimpleArgsWrapper([0.7], ripl=ripl, requestCounts=requestCounts)
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
