def isScopeSpec(exp):
  return isinstance(exp,list) and exp[0] == "scope"

def evalScope(exp):
  assert exp[0] == "scope"
  # Scopes are always literal for now
  { exp[1] : exp[2] }

def scopeUnion(scopes):
  def valMerge(v1, v2):
    raise Exception("Assigning one node to two blocks in the same scope")
  return reduce(lambda ans, scope: mergeWith(ans, scope, valMerge), scopes)

def mergeWith(d1, d2, merge):
  result = dict(d1.iteritems())
  for k,v in d2.iteritems():
    if k in result:
      result[k] = merge(result[k], v)
    else:
      result[k] = v
  return result
