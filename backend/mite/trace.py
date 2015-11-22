class Trace(object):
    def has_own_prng(self): return False

    def extractValue(self, id):
        print 'extractValue', id
        return None

    def eval(self, id, exp):
        print 'eval', id, exp

    def uneval(self, id):
        print 'uneval', id

    def bindInGlobalEnv(self, sym, id):
        print 'bindInGlobalEnv', sym, id

    def observe(self, id, val):
        print 'observe', id, val

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
