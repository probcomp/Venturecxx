# Framework for writing macros that resugar errors.

from types import MethodType
import venture.value.dicts as v

class Macro(object):
  def __init__(self, predicate=None, expander=None):
    self.predicate = predicate
    self.expander = expander

  def applies(self, exp):
    return self.predicate(exp)
  
  def expand(self, exp):
    return self.expander(exp)

class Sugar(object):
  def desugared(self):
    """The desugared expression."""
    raise Exception("Not implemented!")
  
  def desugar_index(self, index):
    """Desugar an expression index."""
    raise Exception("Not implemented!")
  
  def resugar_index(self, index):
    """Transform the desugared expression index back into a sugared one."""
    raise Exception("Not implemented!")

def isLiteral(exp):
  return isinstance(exp, (basestring, dict))

class LiteralMacro(Macro):
  def applies(self, exp):
    return isLiteral(exp)
  def expand(self, exp):
    return LiteralSugar(exp)

class LiteralSugar(Sugar):
  def __init__(self, literal):
    self.literal = literal
  def desugared(self):
    return self.literal
  def desugar_index(self, index):
    assert(len(index) == 0)
    return index
  def resugar_index(self, index):
    assert(len(index) == 0)
    return index

class ListMacro(Macro):
  def applies(self, exp):
    return isinstance(exp, list)
  def expand(self, exp):
    return ListSugar(map(expand, exp))

class ListSugar(Sugar):
  def __init__(self, exp):
    self.exp = exp
  def desugared(self):
    return [e.desugared() for e in self.exp]
  def desugar_index(self, index):
    if len(index) == 0:
      return index
    return index[:1] + self.exp[index[0]].desugar_index(index[1:])
  def resugar_index(self, index):
    if len(index) == 0:
      return index
    return index[:1] + self.exp[index[0]].resugar_index(index[1:])

def traverse(exp):
  if isinstance(exp, list):
    for i, e in enumerate(exp):
      for j, f in traverse(e):
        yield [i] + j, f
  else: yield [], exp

def isSym(exp):
  return isinstance(exp, (str, int))

def bind(pattern, exp):
  if isinstance(pattern, list):
    bindings = {}
    for i, p in enumerate(pattern):
      bindings.update(bind(p, exp[i]))
    return bindings
  return {pattern: exp}

def sub(bindings, template):
  if isinstance(template, list):
    return [sub(bindings, t) for t in template]
  if isSym(template) and template in bindings:
    return bindings[template]
  return template

class SyntaxRule(Macro):
  """Tries to be scheme's define-syntax-rule."""
  def __init__(self, pattern, template):
    self.name = pattern[0]
    self.pattern = pattern
    self.template = template
    
    patternIndeces = {sym: index for index, sym in traverse(pattern) if isSym(sym)}
    templateIndeces = {sym: index for index, sym in traverse(template) if isSym(sym)}
    
    self.desugar = lambda index: replace(pattern, templateIndeces, index)
    self.resugar = lambda index: replace(template, patternIndeces, index)
    
  def applies(self, exp):
    return isinstance(exp, list) and len(exp) > 0 and exp[0] == self.name
  
  def expand(self, exp):
    bindings = bind(self.pattern, exp)
    subbed = sub(bindings, self.template)
    expanded = expand(subbed)
    return SubSugar(expanded, self.desugar, self.resugar)

def replace(exp, indexMap, index):
  i = 0
  while isinstance(exp, list):
    if i == len(index):
      return []
    exp = exp[index[i]]
    i += 1
  
  if isSym(exp) and exp in indexMap:
    return indexMap[exp] + index[i:]
  
  return []

class SubSugar(Sugar):
  def __init__(self, sugar, desugar, resugar):
    self.sugar = sugar
    self.desugar = desugar
    self.resugar = resugar
  def desugared(self):
    return self.sugar.desugared()
  def desugar_index(self, index):
    index = self.desugar(index)
    return self.sugar.desugar_index(index)
  def resugar_index(self, index):
    index = self.sugar.resugar_index(index)
    return self.resugar(index)

def LetExpand(exp):
  n = len(exp[1])
  syms = ['__sym%d__' % i for i in range(n)]
  vals = ['__val%d__' % i for i in range(n)]
  pattern = ['let', map(list, zip(syms, vals)), 'body']
  template = 'body'
  for i in reversed(range(n)):
    template = [['lambda', [syms[i]], template], vals[i]]
  return SyntaxRule(pattern, template).expand(exp)

def arg0(name):
  def applies(exp):
    return isinstance(exp, list) and len(exp) > 0 and exp[0] == name
  return applies
  
identityMacro = SyntaxRule(['identity', 'exp'], ['lambda', [], 'exp'])
lambdaMacro = SyntaxRule(['lambda', 'args', 'body'], ['make_csp', ['quote', 'args'], ['quote', 'body']])
ifMacro = SyntaxRule(['if', 'predicate', 'consequent', 'alternative'], [['biplex', 'predicate', ['lambda', [], 'consequent'], ['lambda', [], 'alternative']]])
andMacro = SyntaxRule(['and', 'exp1', 'exp2'], ['if', 'exp1', 'exp2', v.boolean(False)])
orMacro = SyntaxRule(['or', 'exp1', 'exp2'], ['if', 'exp1', v.boolean(True), 'exp2'])
letMacro = Macro(arg0("let"), LetExpand)

macros = [identityMacro, lambdaMacro, ifMacro, andMacro, orMacro, letMacro, ListMacro(), LiteralMacro()]

def expand(exp):
  for macro in macros:
    if macro.applies(exp):
      return macro.expand(exp)
  raise Exception("Could not match " + str(exp))

def desugar_expression(exp):
  return expand(exp).desugared()

def sugar_expression_index(exp, index):
  return expand(exp).resugar_index(index)

def desugar_expression_index(exp, index):
  return expand(exp).desugar_index(index)

def testLiteral():
  sugar = expand('0')
  print sugar.desugared()

def testList():
  sugar = expand([['+', '1', ['*', '2', '3']]])
  print sugar.desugared()
  print sugar.resugar_index([0, 2, 0])

def testLambda():
  sugar = expand(['lambda', ['x'], ['+', 'x', 'x']])
  print sugar.desugared()
  print sugar.resugar_index([2, 1, 2])

def testIf():
  sugar = expand(['if', ['flip'], '0', '1'])
  print sugar.desugared()
  print sugar.resugar_index([0, 3, 2, 1])

def testAnd():
  sugar = expand(['and', '1', '2'])
  print sugar.desugared()
  print sugar.resugar_index([0, 1])
  print sugar.resugar_index([0, 2, 2, 1])

def testOr():
  sugar = expand(['or', '1', '2'])
  print sugar.desugared()
  print sugar.resugar_index([0, 1])
  print sugar.resugar_index([0, 3, 2, 1])

def testLet():
  sugar = expand(['let', [['a', '1'], ['b', '2']], ['+', 'a', 'b']])
  print sugar.desugared()
  print sugar.resugar_index([0, 1, 1, 0])
  print sugar.resugar_index([1])
  print sugar.resugar_index([0, 2, 1, 0, 1, 1, 0])
  print sugar.resugar_index([0, 2, 1, 1])
  
  print sugar.resugar_index([0, 2, 1, 0, 2, 1])

if __name__ == '__main__':
  testLiteral()
  testList()
  testLambda()
  testIf()
  testAnd()
  testOr()
  testLet()
