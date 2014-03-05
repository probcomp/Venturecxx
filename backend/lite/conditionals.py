from psp import PSP
from request import Request,ESR
import value as v

# TODO This is used very little because the stack expands if to biplex.  Flush?
class BranchRequestPSP(PSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    assert not args.operandValues[0] is None
    if args.operandValues[0].getBool(): expIndex = 1
    else: expIndex = 2

    exp = v.ExpressionType().asPython(args.operandValues[expIndex])
    return Request([ESR(args.node,exp,args.env)])

  def description(self,name):
    return "(%s <bool> <exp1> <exp2>) -> <object>\n  Evaluates either exp1 or exp2 in the current environment and returns the result." % name
