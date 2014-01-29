from psp import PSP

def mergeWith(d1, d2, merge):
  result = dict(d1.iteritems())
  for k,v in d2.iteritems():
    if k in result:
      result[k] = merge(result[k], v)
    else:
      result[k] = v
  return result

class ScopeIncludeOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[2]
  def description(self,name):
    return "(%s <scope> <block> <object>) -> <object>\n  Identity function at runtime, but tags the subexpression creating the object as being within the given scope and block." % name
