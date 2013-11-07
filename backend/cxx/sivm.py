from libtrace import Trace
from venture.exception import VentureException

# Our SIVM is not a fully conforming SIVM, for reasons I hope
# the person reading this will understand better than I do.
# For one, the directives take strings and does the parsing,
# which can easily be changed. Venture also has some kind of
# type system which this does not support explicitly.

# A note on addresses: addresses are lists (though they are 
# also converted to strings before hashing), and the definite
# families begin with [<directiveId>]. 

# Suppose the SP created at address SP-ADDR requests an LIA
# with local address LIA-ADDR. Then the full address of that LIA 
# would be SP-ADDR + [<sp>] + LIA-NAME (where + is append).


class SIVM:

    def __init__(self):
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    def nextBaseAddr(self):
        self.directiveCounter += 1
        return self.directiveCounter

    def assume(self,id,datum):
        baseAddr = self.nextBaseAddr()

        self.trace.eval(baseAddr,datum);
        self.trace.bindInGlobalEnv(id,baseAddr)

        self.directives[self.directiveCounter] = ["assume",id,datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))
        
    def predict(self,datum):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,datum)

        self.directives[self.directiveCounter] = ["predict",datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))

    def observe(self,datum,val):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,datum)
        logDensity = self.trace.observe(baseAddr,val)

        # TODO check for -infinity? Throw an exception?
        if logDensity == float("-inf"): raise VentureException("invalid_constraint", "Observe failed to constrain", expression=datum, value=val)
        self.directives[self.directiveCounter] = ["observe",datum,val]

        return self.directiveCounter

    def forget(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot forget a non-existent directive id", argument=directiveId)
        directive = self.directives[directiveId]
        if directive[0] == "assume": raise VentureException("invalid_argument", "Cannot forget an ASSUME directive", argument=directiveId)
        if directive[0] == "observe": self.trace.unobserve(str(directiveID))
        self.trace.unevalFamily(str(directiveId))
        del self.directives[directiveId]
    
    def report_value(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot report a non-existent directive id", argument=directiveId)
        return self.trace.extractValue(directiveId)

    def clear(self):
        del self.trace
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    # This could be parameterized to call different inference programs.
    def infer(self,N=1):
        self.trace.infer(N)
    
    # FIXME: These are not properly implemented
    
    def logscore(self):
        raise VentureException("not_implemented", "logscore() is not implemented")

    def get_entropy_info(self):
       raise VentureException("not_implemented", "get_entropy_info() is not implemented")

    def get_seed(self):
        return self.trace.get_seed()

    def set_seed(self, seed):
        self.trace.set_seed(seed)

