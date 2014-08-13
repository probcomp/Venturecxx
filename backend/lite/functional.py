from psp import DeterministicPSP
from env import VentureEnvironment
from request import Request, ESR
from value import VentureArray

class ApplyRequestPSP(DeterministicPSP):
    def simulate(self, args):
        operator = args.operandValues[0]
        operands = args.operandValues[1]
        exp = [operator] + operands
        env = VentureEnvironment()
        return Request([ESR(args.node, exp, env)])

    def description(self, name):
        return "(%s func vals) returns the result of applying a variadic function to an array of operands" % name

class ArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        operator = args.operandValues[0]
        operands = args.operandValues[1]
        exps = [[operator, operand] for operand in operands]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, env) for i, exp in enumerate(exps)])

    def description(self, name):
        return "(%s func vals) returns the results of applying a function to each value in an array" % name

class ESRArrayOutputPSP(DeterministicPSP):
    def simulate(self, args):
        return VentureArray(args.esrValues)
