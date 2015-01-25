from psp import DeterministicPSP, TypedPSP
from request import Request,ESR
from sp import SPType
import value as v

# TODO This is used very little because the stack expands if to biplex.  Flush?
class BranchRequestPSP(DeterministicPSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    assert not args.operandValues[0] is None
    if args.operandValues[0]:
      expIndex = 1
    else:
      expIndex = 2
    exp = args.operandValues[expIndex]
    # point to the source code location of the expression
    addr = args.operandNodes[expIndex].address.last.append(1)
    return Request([ESR(args.node,exp,addr,args.env)])

  def description(self,name):
    return "%s evaluates either exp1 or exp2 in the current environment and returns the result.  Is itself deterministic, but the chosen expression may involve a stochastic computation." % name

def branch_request_psp():
  return TypedPSP(BranchRequestPSP(), SPType([v.BoolType(), v.ExpressionType(), v.ExpressionType()], v.RequestType("<object>")))
