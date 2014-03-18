from psp import PSP

class ScopeIncludeOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[2]
  def gradientOfSimulate(self, _args, direction): return [0, 0, direction]
  def canAbsorb(self, _trace, appNode, parentNode): return parentNode != appNode.operandNodes[2]
  
  def description(self,name):
    return "%s :: <SP <scope> <block> <object> -> <object>>\n  Returns its third argument unchanged at runtime, but tags the subexpression creating the object as being within the given scope and block." % name
