import venture.lite.value as v

_builtInSPs = {}

def registerBuiltinSP(name, sp):
  _builtInSPs[name] = sp

def builtInSPs():
  return _builtInSPs
