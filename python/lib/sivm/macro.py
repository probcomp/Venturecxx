# Framework for writing macros that resugar errors.

from types import MethodType
import venture.value.dicts as v

class Macro(object):
  def applies(self, expr):
    raise Exception("Not implemented!")
  
  def expand(self, expr):
    raise Exception("Not implemented!")

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
    i = index[0]
    return [i] + self.expr[i].resugar(index[1:])

def traverse(expr):
  if isinstance(expr, list):
    for i, e in enumerate(expr):
      for j, f in traverse(e):
        yield [i] + j, f
  yield [], expr

def index(expr, i):
  if len(i) == 0:
    return expr
  return index(expr[i[0]], i[1:])

def substitute(expr, pattern):
  if isinstance(pattern, list):
    return [substitute(expr, p) for p in pattern]
  if isinstance(pattern, tuple):
    return index(expr, pattern)
  return pattern

class SubMacro(Macro):
  def __init__(self, pattern):
    self.pattern = pattern
    self.inverse = [(i,list(tup)) for (i, tup) in traverse(pattern) if isinstance(tup, tuple)]
  
  def expand(self, expr):
    sub = substitute(expr, self.pattern)
    #print sub
    return SubSugar(expand(sub), self.inverse)

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

def kwMacro(keyword, macro):
  def applies(self, expr):
    return isinstance(expr, list) and len(expr) > 0 and expr[0] == keyword
  macro.applies = MethodType(applies, macro)
  return macro

lambdaMacro = kwMacro("lambda", SubMacro(['make_csp', ['quote', (1,)], ['quote', (2,)]]))
ifMacro = kwMacro("if", SubMacro([['biplex', (1,), ['lambda', [], (2,)], ['lambda', [], (3,)]]]))
andMacro = kwMacro("and", SubMacro(['if', (1,), (2,), v.boolean(True)]))
orMacro = kwMacro("or", SubMacro(['if', (1,), v.boolean(True), (2,)]))

macros = [lambdaMacro, ifMacro, andMacro, orMacro, ListMacro(), LiteralMacro()]

def expand(expr):
  for macro in macros:
    if macro.applies(expr):
      return macro.expand(expr)
  raise Exception("Could not match " + str(expr))

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

if __name__ == '__main__':
  testLiteral()
  testList()
  testLambda()
  testIf()
  testAnd()
  testOr()

