from psp import PSP

class ScopeIncludeOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[2]
  def canAbsorb(self,trace,appNode,parentNode): return parentNode != appNode.operandNodes[2]
  
  def description(self,name):
    return "(%s <scope> <block> <object>) -> <object>\n  Identity function at runtime, but tags the subexpression creating the object as being within the given scope and block." % name
