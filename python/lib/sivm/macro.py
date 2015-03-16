# Macros that resyntax errors.
# For a description of the framework, see macro_system.py

from venture.exception import VentureException
from macro_system import Macro, Syntax, getSym, register_macro, expand
from pattern_language import SyntaxRule
import venture.value.dicts as v

def isLiteral(exp):
  return isinstance(exp, (basestring, dict))

class LiteralMacro(Macro):
  def applies(self, exp):
    return isLiteral(exp)
  def expand(self, exp):
    return LiteralSyntax(exp)

class LiteralSyntax(Syntax):
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
    return isinstance(exp, list) or v.is_stack_dict_of_type("array", exp)
  def expand(self, exp):
    exp = self._canonicalize(exp)
    expanded = []
    for i, s in enumerate(exp):
      try:
        expanded.append(expand(s))
      except VentureException as e:
        e.data['expression_index'].insert(0, i)
        raise
    return ListSyntax(expanded)
  def _canonicalize(self, exp):
    if isinstance(exp, list):
      return exp
    else:
      return exp["value"] # Should always be an array literal

class ListSyntax(Syntax):
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

# Let is not directly a SyntaxRule because the pattern language does
# not support repetition.  Instead, expansion of a let form computes a
# ground pattern and template pair of the right size and dynamically
# forms and uses a SyntaxRule out of that.
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

for m in [identityMacro, lambdaMacro, ifMacro, andMacro, orMacro, letMacro, ListMacro(), LiteralMacro()]:
  register_macro(m)
