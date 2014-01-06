def isVariable(exp): return isinstance(exp,str)
def isSelfEvaluating(exp): return not isinstance(exp,list)
def isQuotation(exp): return exp[0] == "quote"    
def textOfQuotation(exp): return exp[1] 
def getOperator(exp): return exp[0]
def getOperands(exp): return exp[1:]
