from psp import PSP
from request import Request,ESR

class BranchRequestPSP(PSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    if args.operandValues[0]: expIndex = 1
    else: expIndex = 2

    exp = args.operandValues[expIndex]
    return Request([ESR(args.node,exp,args.env)])

  def description(self,name):
    return "(%s <bool> <exp1> <exp2>) -> <object>\n  Evaluates either exp1 or exp2 in the current environment" % name

class BiplexOutputPSP(PSP):
  def simulate(self,args):
    if args.operandValues[0]:
      return args.operandValues[1]
    else:
      return args.operandValues[2]

  def description(self,name):
    return "(%s <bool> <object1> <object2>) -> <object>" % name
