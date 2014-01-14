def mergeWith(d1, d2, merge):
  result = dict(d1.iteritems())
  for k,v in d2.iteritems():
    if k in result:
      result[k] = merge(result[k], v)
    else:
      result[k] = v
  return result

def isScopeApply(exp):
  return isinstance(exp,list) and exp[0] == "scope_include"

def scopeApplicand(exp):
  assert exp[0] == "scope_include"
  return exp[3]

def scopeSpecOf(exp):
  assert exp[0] == "scope_include"
  return { exp[1] : exp[2] }
