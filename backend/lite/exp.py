from scope import *

def isVariable(exp): return isinstance(exp,str)
def isSelfEvaluating(exp): return not isinstance(exp,list)
def isQuotation(exp): return exp[0] == "quote"    
def textOfQuotation(exp): return exp[1] 
def getOperator(exp): return exp[0]
def getOperands(exp): return [sub for sub in exp[1:] if not isScopeSpec(sub)]

def expScopes(exp): return scopeUnion([evalScope(sub) for sub in exp if isScopeSpec(sub)])
