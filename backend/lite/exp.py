def isVariable(exp): return isinstance(exp,str)
def isSelfEvaluating(exp): return not isinstance(exp,list)

def isQuotation(exp): 
  assert isinstance(exp,list)
  assert len(exp) > 0
  return exp[0] == "quote"

def textOfQuotation(exp): 
  assert len(exp) > 1
  return exp[1] 

def getOperator(exp): 
  assert isinstance(exp,list)
  assert len(exp) > 0
  return exp[0]

def getOperands(exp): return exp[1:]
