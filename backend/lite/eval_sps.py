from psp import DeterministicPSP
from env import VentureEnvironment
from request import Request,ESR
import value as v

class EvalRequestPSP(DeterministicPSP):
  def simulate(self,args):
    exp = v.ExpressionType().asPython(args.operandValues[0])
    env = args.operandValues[1]
    return Request([ESR(args.node,exp,env)])
  def description(self,name):
    return "%s :: <SP <exp> <env> -> <object>>\n  Evaluates the given expression in the given environment and returns the result.  Is itself deterministic, but the given expression may involve a stochasitc computation." % name

class ExtendEnvOutputPSP(DeterministicPSP):
  def simulate(self,args): 
    env = args.operandValues[0]
    sym = args.operandValues[1].getSymbol()
    node = args.operandNodes[2]
    return VentureEnvironment(env,[sym],[node])
  def description(self,name):
    return "%s :: <SP <env> <symbol> <object> -> <env>>\n  Returns an extension of the given environment where the given symbol is bound to the given object" % name
