from venture.lite.env import VentureEnvironment
from venture.lite.psp import DeterministicPSP, TypedPSP
from venture.lite.sp import VentureSPRecord, SPType
import venture.lite.types as t

from venture.mite.sp import SimpleRequestingSP, ESR

# copied from csp.py, modified to return a new-style SP
class MakeCSPOutputPSP(DeterministicPSP):
    def simulate(self, args):
        (ids, exp) = args.operandValues()
        # point to the desugared source code location of lambda body
        addr = args.operandNodes[1].address.last.append(1)
        return VentureSPRecord(CompoundSP(ids, exp, addr, args.env))

make_csp = TypedPSP(MakeCSPOutputPSP(), SPType(
    [t.HomogeneousArrayType(t.SymbolType()), t.ExpressionType()],
    t.AnyType("a compound SP")))

class CompoundSP(SimpleRequestingSP):
    def __init__(self, ids, exp, addr, env):
        self.ids = ids
        self.exp = exp
        self.addr = addr
        self.env = env

    def request(self, args, constraint):
        if len(self.ids) != len(args.operandNodes):
            raise Exception("Wrong number of arguments: compound takes exactly %d arguments, got %d." % (len(self.ids), len(args.operandNodes)))
        extendedEnv = VentureEnvironment(self.env, self.ids, args.operandNodes)
        return ESR(args.node, self.exp, self.addr, extendedEnv)

