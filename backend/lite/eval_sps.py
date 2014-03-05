from psp import PSP
from env import VentureEnvironment
from request import Request,ESR
import value as v

class EvalRequestPSP(PSP):
  def simulate(self,args):
    exp = v.ExpressionType().asPython(args.operandValues[0])
    env = args.operandValues[1]
    return Request([ESR(args.node,exp,env)])
  def description(self,name):
    return "(%s <exp> <env>) -> <object>\n  Evaluates the given expression in the given environment." % name

class GetEmptyEnvOutputPSP(PSP):
  def simulate(self,args): return VentureEnvironment()
  def description(self,name):
    return "(%s) -> <env>" % name

class ExtendEnvOutputPSP(PSP):
  def simulate(self,args): 
    env = args.operandValues[0]
    sym = args.operandValues[1].getSymbol()
    node = args.operandNodes[2]
    return VentureEnvironment(env,[sym],[node])
  def description(self,name):
    return "(%s <env> <symbol> <object>) -> <env>" % name
