from utils import override
from psp import DeterministicPSP, TypedPSP

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

def isScopeIncludeOutputPSP(thing):
  return isinstance(thing, ScopeIncludeOutputPSP) or \
    (isinstance(thing, TypedPSP) and isScopeIncludeOutputPSP(thing.psp))

class ScopeExcludeOutputPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self,args): return args.operandValues[1]
  @override(DeterministicPSP)
  def gradientOfSimulate(self, _args, _value, direction): return [0, direction]
  @override(DeterministicPSP)
  def canAbsorb(self, _trace, appNode, parentNode): return parentNode != appNode.operandNodes[1]
  
  @override(DeterministicPSP)
  def description(self,name):
    return "%s returns its second argument unchanged at runtime, but tags the subexpression creating the object as being outside the given scope." % name

def isScopeExcludeOutputPSP(thing):
  return isinstance(thing, ScopeExcludeOutputPSP) or \
    (isinstance(thing, TypedPSP) and isScopeExcludeOutputPSP(thing.psp))
