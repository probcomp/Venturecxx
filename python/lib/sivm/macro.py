# Framework for writing macros that resugar errors.

from types import MethodType
import venture.value.dicts as v

class Macro(object):
  def __init__(self, predicate=None, expander=None):
    self.predicate = predicate
    self.expander = expander

  def applies(self, expr):
    return self.predicate(expr)
  
  def expand(self, expr):
    return self.expander(expr)

class Sugar(object):
  def desugar(self):
    raise Exception("Not implemented!")
  def resugar(self, index):
    raise Exception("Not implemented!")

class LiteralMacro(Macro):
  def applies(self, expr):
    return isinstance(expr, (basestring, dict))
  def expand(self, expr):
    return LiteralSugar(expr)

class LiteralSugar(Sugar):
  def __init__(self, literal):
    self.literal = literal
  def desugar(self):
    return self.literal
  def resugar(self, index):
    assert(len(index) == 0)
    return index

class ListMacro(Macro):
  def applies(self, expr):
    return isinstance(expr, list)
  def expand(self, expr):
    return ListSugar(map(expand, expr))

class ListSugar(Sugar):
  def __init__(self, expr):
    self.expr = expr
  def desugar(self):
    return [e.desugar() for e in self.expr]
  def resugar(self, index):
    if len(index) == 0:
      return index
    return index[:1] + self.expr[index[0]].resugar(index[1:])

def traverse(expr):
  if isinstance(expr, list):
    for i, e in enumerate(expr):
      for j, f in traverse(e):
        yield [i] + j, f
  else: yield [], expr

def index(i, expr):
  """Index into an expression."""
  if len(i) == 0:
    return expr
  return index(i[1:], expr[i[0]])

def substitute(expr, pattern):
  if isinstance(pattern, list):
    return [substitute(expr, p) for p in pattern]
  if isinstance(pattern, tuple):
    return index(pattern, expr)
  return pattern

def PatternExpand(pattern):
  inverse = [(i,list(tup)) for (i, tup) in traverse(pattern) if isinstance(tup, tuple)]
  
  def expander(expr):
    sub = substitute(expr, pattern)
    #print sub
    return SubSugar(expand(sub), inverse)
  
  return expander


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
  if template in bindings:
    return bindings[template]
  return template

class SyntaxRule(Macro):
  """My interpretation of scheme's define-syntax-rule."""
  def __init__(self, pattern, template):
    self.name = pattern[0]
    self.pattern = pattern
    self.template = template
    
    patternMap = {sym: index for index, sym in traverse(pattern) if isinstance(sym, str)}
    self.inverse = [(index, patternMap[sym]) for index, sym in traverse(template) if sym in patternMap]
  
  def applies(self, exp):
    return isinstance(exp, list) and len(exp) > 0 and exp[0] == self.name
  
  def expand(self, exp):
    bindings = bind(self.pattern, exp)
    subbed = sub(bindings, self.template)
    expanded = expand(subbed)
    return SubSugar(expanded, self.inverse)

def prefix(l1, l2):
  if len(l1) > len(l2):
    return False
  for e1, e2 in zip(l1, l2):
    if e1 != e2:
      return False
  return True

class SubSugar(Sugar):
  def __init__(self, sugar, inverse):
    self.sugar = sugar
    self.inverse = inverse
  def desugar(self):
    return self.sugar.desugar()
  def resugar(self, index):
    index = self.sugar.resugar(index)
    for i, j in self.inverse:
      if prefix(i, index):
        return j + index[len(i):]
    return index

def LetExpand(expr):
  pattern = (2,)
  for index in reversed(range(len(expr[1]))):
    pattern = [['lambda', [(1, index, 0)], pattern], (1, index, 1)]
  return PatternExpand(pattern)(expr)

def arg0(keyword):
  def applies(expr):
    return isinstance(expr, list) and len(expr) > 0 and expr[0] == keyword
  return applies

lambdaMacro = SyntaxRule(['lambda', 'args', 'body'], ['make_csp', ['quote', 'args'], ['quote', 'body']])
ifMacro = Macro(arg0("if"), PatternExpand([['biplex', (1,), ['lambda', [], (2,)], ['lambda', [], (3,)]]]))
andMacro = Macro(arg0("and"), PatternExpand(['if', (1,), (2,), v.boolean(False)]))
orMacro = Macro(arg0("or"), PatternExpand(['if', (1,), v.boolean(True), (2,)]))
letMacro = Macro(arg0("let"), LetExpand)

macros = [lambdaMacro, ifMacro, andMacro, orMacro, letMacro, ListMacro(), LiteralMacro()]

def expand(expr):
  for macro in macros:
    if macro.applies(expr):
      return macro.expand(expr)
  raise Exception("Could not match " + str(expr))

def desugar_expression(expr):
  return expand(expr).desugar()

def testLiteral():
  sugar = expand('0')
  print sugar.desugar()

def testList():
  sugar = expand([['+', '1', ['*', '2', '3']]])
  print sugar.desugar()
  print sugar.resugar([0, 2, 0])

def testLambda():
  sugar = expand(['lambda', ['x'], ['+', 'x', 'x']])
  print sugar.desugar()
  print sugar.resugar([2, 1, 2])

def testIf():
  sugar = expand(['if', ['flip'], '0', '1'])
  print sugar.desugar()
  print sugar.resugar([0, 3, 2, 1])

def testAnd():
  sugar = expand(['and', '1', '2'])
  print sugar.desugar()
  print sugar.resugar([0, 1])
  print sugar.resugar([0, 2, 2, 1])

def testOr():
  sugar = expand(['or', '1', '2'])
  print sugar.desugar()
  print sugar.resugar([0, 1])
  print sugar.resugar([0, 3, 2, 1])

def testLet():
  sugar = expand(['let', [['a', '1'], ['b', '2']], ['+', 'a', 'b']])
  print sugar.desugar()
  print sugar.resugar([0, 1, 1, 0])
  print sugar.resugar([1])
  print sugar.resugar([0, 2, 1, 0, 1, 1, 0])
  print sugar.resugar([0, 2, 1, 1])
  
  print sugar.resugar([0, 2, 1, 0, 2, 1])

if __name__ == '__main__':
  testLiteral()
  testList()
  testLambda()
  testIf()
  testAnd()
  testOr()
  testLet()
