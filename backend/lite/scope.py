from utils import override
from psp import DeterministicPSP

class ScopeIncludeOutputPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self,args): return args.operandValues[2]
  @override(DeterministicPSP)
  def gradientOfSimulate(self, _args, _value, direction): return [0, 0, direction]
  @override(DeterministicPSP)
  def canAbsorb(self, _trace, appNode, parentNode): return parentNode != appNode.operandNodes[2]
  
  @override(DeterministicPSP)
  def description(self,name):
    return "%s returns its third argument unchanged at runtime, but tags the subexpression creating the object as being within the given scope and block." % name
