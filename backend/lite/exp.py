from scope import *

def isVariable(exp): return isinstance(exp,str)
def isSelfEvaluating(exp): return not isinstance(exp,list)
def isQuotation(exp): return exp[0] == "quote"    
def textOfQuotation(exp): return exp[1] 
def getOperator(exp):
  if isScopeApply(exp):
    return getOperator(scopeApplicand(exp))
  else:
    return exp[0]
def getOperands(exp):
  if isScopeApply(exp):
    return getOperands(scopeApplicand(exp))
  else:
    return exp[1:]

def expScopes(exp):
  def valMerge(v1, v2):
    raise Exception("Assigning one node to two blocks in the same scope")
  if isScopeApply(exp):
    return mergeWith(scopeSpecOf(exp), expScopes(scopeApplicand(exp)), valMerge)
  else:
    return {}
