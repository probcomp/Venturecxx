from psp import PSP, TypedPSP
from request import Request,ESR
import value as v

# TODO This is used very little because the stack expands if to biplex.  Flush?
class BranchRequestPSP(PSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    assert not args.operandValues[0] is None
    if args.operandValues[0]:
      expIndex = 1
    else:
      expIndex = 2
    exp = args.operandValues[expIndex]
    return Request([ESR(args.node,exp,args.env)])

  def description(self,name):
    return "%s evaluates either exp1 or exp2 in the current environment and returns the result.  Is itself deterministic, but the chosen expression may involve a stochastic computation." % name

def branch_request_psp():
  return TypedPSP([v.BoolType(), v.ExpressionType(), v.ExpressionType()], v.RequestType("<object>"), BranchRequestPSP())
