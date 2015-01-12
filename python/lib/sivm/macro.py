# Framework for writing macros that resugar errors.

# This code uses terminology that is slightly non-standard from the
# point of view of traditional macro systems.  Specifically:
#
# - a "macro" is an object that may transform an expression to a
#   "sugar" object.  Spiritually:
#
#     type Macro = Expression -> Maybe Sugar
#
# - a "sugar" is an object that can emit a macroexpanded expression,
#   and implements an isomorphism between indexes on the expanded and
#   unexpanded versions of the expression.  Spiritually:
#
#     type Sugar = (Expression, Index -> Index, Index -> Index)
#
# - an "index" is a path through an expression that indicates a
#   subexpression of interest (used for error reporting).
#   Spiritually:
#
#     type Index = Expression -> Expression
#
#   but they are represented explicitly, and transformed by sugars.
#
# Note that there is no notional separation between "macroexpand-1"
# and "macroexpand" (to use vocabulary from Common Lisp): the "sugar"
# object produced by one invocation of a "macro" is responsible for
# producing a fully macroexpanded expression.  This is accomplished by
# recursively invoking macroexpansion on subexpressions.
#
# Given that, macroexpansion proceeds simply by trying all known
# macros in order, using the result of the first that produces
# something -- see the top-level function `expand`.

from venture.exception import VentureException
import venture.value.dicts as v

class Macro(object):
  def __init__(self, predicate=None, expander=None, desc=None):
    self.predicate = predicate
    self.expander = expander
    self.desc = desc

  def applies(self, exp):
    return self.predicate(exp)
  
  def expand(self, exp):
    return self.expander(exp)

class Sugar(object):
  def desugared(self):
    """The desugared expression."""
    raise Exception("Not implemented!")
  
  def desugar_index(self, _index):
    """Desugar an expression index."""
    raise Exception("Not implemented!")
  
  def resugar_index(self, _index):
    """Transform the desugared expression index back into a sugared one."""
    raise Exception("Not implemented!")

def isLiteral(exp):
  return isinstance(exp, (basestring, dict))

def isSym(exp):
  return isinstance(exp, str)

def getSym(exp):
  if isSym(exp):
    return exp
  if isinstance(exp, dict):
    if exp['type'] == 'symbol':
      return exp['value']
  return None

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
    assert len(index) == 0
    return index
  def resugar_index(self, index):
    if len(index) != 0:
      print "Warning: bad literal resugar index."
      return []
    return index

class ListMacro(Macro):
  def applies(self, exp):
    return isinstance(exp, list)
  def expand(self, exp):
    expanded = []
    for i, s in enumerate(exp):
      try:
        expanded.append(expand(s))
      except VentureException as e:
        e.data['expression_index'].insert(0, i)
        raise
    return ListSugar(expanded)

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

def verify(pattern, exp, context):
  """Verifies that the given expression matches the pattern in form."""
  if isinstance(pattern, list):
    if not isinstance(exp, list):
      raise VentureException('parse',
        'Invalid expression in %s -- expected list!' % (context,),
        expression_index=[])
    if len(exp) != len(pattern):
      raise VentureException('parse',
        'Invalid expression in %s -- expected length %d' %
          (context, len(pattern)),
        expression_index=[])
    for index, (p, e) in enumerate(zip(pattern, exp)):
      try:
        verify(p, e, context)
      except VentureException as e:
        e.data['expression_index'].insert(0, index)
        raise

class SyntaxRule(Macro):
  """Tries to be scheme's define-syntax-rule."""
  def __init__(self, pattern, template, desc=None):
    self.name = pattern[0]
    self.pattern = pattern
    self.template = template
    self.desc = desc
    
    patternIndeces = {sym: index for index, sym in traverse(pattern) if isSym(sym)}
    templateIndeces = {sym: index for index, sym in traverse(template) if isSym(sym)}
    
    self.desugar = lambda index: replace(pattern, templateIndeces, index)
    self.resugar = lambda index: replace(template, patternIndeces, index)
    
  def applies(self, exp):
    return isinstance(exp, list) and len(exp) > 0 and getSym(exp[0]) == self.name
  
  def expand(self, exp):
    verify(self.pattern, exp, self.pattern[0])
    try:
      bindings = bind(self.pattern, exp)
      subbed = sub(bindings, self.template)
      expanded = expand(subbed)
      return SubSugar(expanded, self.desugar, self.resugar)
    except VentureException as e:
      e.data['expression_index'] = self.resugar(e.data['expression_index'])
      raise

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
  if len(exp) != 3:
      raise VentureException('parse','"let" statement requires 2 arguments',expression_index=[])
  if not isinstance(exp[1], list):
      raise VentureException('parse','"let" first argument must be a list',expression_index=[1])
  
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
    return isinstance(exp, list) and len(exp) > 0 and getSym(exp[0]) == name
  return applies
  
identityMacro = SyntaxRule(['identity', 'exp'], ['lambda', [], 'exp'])
lambdaMacro = SyntaxRule(['lambda', 'args', 'body'],
                         ['make_csp', ['quote', 'args'], ['quote', 'body']],
                         desc="""\
- `(lambda (param ...) body)`: Construct a procedure.

  The formal parameters must be Venture symbols.
  The body must be a Venture expression.
  The semantics are as in Scheme or Church.  Unlike Scheme, the body
  must be a single expression, and creation of variable arity
  procedures is not supported.
""")

ifMacro = SyntaxRule(['if', 'predicate', 'consequent', 'alternative'],
                     [['biplex', 'predicate', ['lambda', [], 'consequent'], ['lambda', [], 'alternative']]],
                     desc="""\
- `(if predicate consequent alternate)`: Branch control.

  The predicate, consequent, and alternate must be Venture expressions.
""")

andMacro = SyntaxRule(['and', 'exp1', 'exp2'],
                      ['if', 'exp1', 'exp2', v.boolean(False)],
                      desc="""- `(and exp1 exp2)`: Short-circuiting and. """)

orMacro = SyntaxRule(['or', 'exp1', 'exp2'],
                     ['if', 'exp1', v.boolean(True), 'exp2'],
                     desc="""- `(or exp1 exp2)`: Short-circuiting or. """)

letMacro = Macro(arg0("let"), LetExpand,
                 desc="""\
- `(let ((param exp) ...) body)`: Evaluation with local scope.

  Each parameter must be a Venture symbol.
  Each exp must be a Venture expression.
  The body must be a Venture expression.
  The semantics are as Scheme's `let*`: each `exp` is evaluated in turn,
  its result is bound to the `param`, and made available to subsequent
  `exp` s and the `body`.
""")

macros = [identityMacro, lambdaMacro, ifMacro, andMacro, orMacro, letMacro, ListMacro(), LiteralMacro()]

def expand(exp):
  for macro in macros:
    if macro.applies(exp):
      return macro.expand(exp)
  raise VentureException('parse', "Unrecognizable expression " + str(exp), expression_index=[])

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

def testVerify():
  try:
    verify(['let', [['__sym0__', '__val0__']], 'body'], ['let', ['a'], 'b'],
      'let')
    print "testVerify() failed!"
  except VentureException as e:
    print e.data['expression_index']

if __name__ == '__main__':
  testLiteral()
  testList()
  testLambda()
  testIf()
  testAnd()
  testOr()
  testLet()
  testVerify()
