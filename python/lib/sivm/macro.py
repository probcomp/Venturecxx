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

def DoExpand(exp):
  if len(exp) == 2:
    # One statement
    pattern = ["do", "stmt"]
    template = "stmt"
  else:
    (_do, statement, rest) = (exp[0], exp[1], exp[2:])
    rest_vars = ["rest_%d" % i for i in range(len(rest))]
    if (type(statement) is list and len(statement) == 3 and type(statement[1]) is dict and
        statement[1]["value"] == "<-"):
      # Binding statement, regular form
      pattern = ["do", ["var", "<-", "expr"]] + rest_vars
      template = ["bind", "expr", ["lambda", ["var"], ["do"] + rest_vars]]
    elif (type(statement) is list and len(statement) == 3 and type(statement[0]) is dict and
        statement[0]["value"] == "<-"):
      # Binding statement, venturescript form
      pattern = ["do", ["<-", "var", "expr"]] + rest_vars
      template = ["bind", "expr", ["lambda", ["var"], ["do"] + rest_vars]]
    else:
      # Non-binding statement
      pattern = ["do", "stmt"] + rest_vars
      template = ["bind_", "stmt", ["lambda", [], ["do"] + rest_vars]]
  return SyntaxRule(pattern, template).expand(exp)

def QuasiquoteExpand(exp):
  import collections
  name_ct = [0] # Explicit box because Python can't mutate locals from closures
  def unique_name(prefix):
    name_ct[0] += 1
    return "%s-%d" % (prefix, name_ct[0])
  def quote_result():
    datum_name = unique_name("datum")
    return (datum_name, ["quote", datum_name], True)
  def qqrecur(exp):
    """Returns a tuple (pattern, template, bool) explaining how to macroexpand this (sub-)expression.

The pattern and template may be used to construct a SyntaxRule object
that will do the right thing (but are returned seprately because
SyntaxRule objects are not directly composable).

The bool is an optimization.  It indicates whether quasiquote reduces
to quote on this expression; if that turns out to be true for all
subexpressions, their expansion can be short-circuited.

    """
    if hasattr(exp, "__iter__") and not isinstance(exp, collections.Mapping):
      if len(exp) > 0 and getSym(exp[0]) == "unquote":
        datum_name = unique_name("datum")
        return ([unique_name("unquote"), datum_name], datum_name, False)
      else:
        answers = [qqrecur(expi) for expi in exp]
        if all([ans[2] for ans in answers]):
          return quote_result()
        else:
          pattern = [answer[0] for answer in answers]
          template = [v.sym("array")] + [answer[1] for answer in answers]
          return (pattern, template, False)
    else:
      return quote_result()
  (pattern, template, _) = qqrecur(exp[1])
  return SyntaxRule(["quasiquote", pattern], template).expand(exp)

def symbol_prepend(prefix, symbol):
  if isinstance(symbol, basestring):
    return prefix + symbol
  else:
    return v.symbol(prefix + symbol["value"])

def quasiquotation_macro(name, desc="", min_size = None, max_size = None):
  def expander(program):
    if min_size is not None:
      assert len(program) >= min_size
    if max_size is not None:
      assert len(program) <= max_size
    pat_names = ["datum-%d" % i for i in range(len(program))]
    pattern = [name] + pat_names[1:]
    template = ["_" + name] + [["quasiquote", pn] for pn in pat_names[1:]]
    return SyntaxRule(pattern, template).expand(program)
  return Macro(arg0(name), expander, desc=desc)

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
letMacro = Macro(arg0("let"), LetExpand, desc="""\
- `(let ((param exp) ...) body)`: Evaluation with local scope.

  Each parameter must be a Venture symbol.
  Each exp must be a Venture expression.
  The body must be a Venture expression.
  The semantics are as Scheme's `let*`: each `exp` is evaluated in turn,
  its result is bound to the `param`, and made available to subsequent
  `exp` s and the `body`.
""")

# Do is not directly a SyntaxRule because the pattern language does
# not support repetition or alternatives.  Instead, expansion of a do
# form computes a ground pattern and template pair of the right shape
# and size and dynamically forms and uses a SyntaxRule out of that.
doMacro = Macro(arg0("do"), DoExpand, desc="""\
- `(do <stmt> <stmt> ...)`: Sequence actions that may return results.

  Each <stmt> except the last may either be

    - a kernel, in which case it is performed and any value it returns
      is dropped, or

    - a binder of the form ``(<variable> <- <kernel>)`` in which case the
      kernel is performed and its value is made available to the remainder
      of the ``do`` form by being bound to the variable.

  The last <stmt> may not be a binder and must be a kernel.  The whole
  ``do`` expression is then a single compound heterogeneous kernel,
  whose value is the value returned by the last <stmt>.

  If you need a kernel that produces a value without doing anything, use
  ``(return <value>)``.  If you need a kernel that does nothing and
  produces no useful value, you can use ``pass``.

  For example, to make a kernel that does inference until some variable
  in the model becomes "true" (why would anyone want to do that?), you
  can write::

      1 [define my_strange_kernel (lambda ()
      2   (do
      3     (finish <- (sample something_from_the_model))
      4     (if finish
      5         pass
      6         (do
      7           (mh default one 1)
      8           (my_strange_kernel)))))]

  Line 3 is a binder for the ``do`` started on line 2, which makes
  ``finish`` a variable usable by the remainder of the procedure.  The
  ``if`` starting on line 4 is a kernel, and is the last statement of
  the outer ``do``.  Line 7 is a non-binder statement for the inner
  ``do``.

  The nomenclature is borrowed from the (in)famous ``do`` notation of
  Haskell.  If this helps you think about it, Venture's ``do`` is
  exactly Haskell ``do``, except there is only one monad, which is
  essentially ``State ModelHistory``.  Randomness and actual i/o are not
  treated monadically, but just executed, which we can get away with
  because Venture is strict and doesn't aspire to complete functional
  purity.""")

qqMacro = Macro(arg0("quasiquote"), QuasiquoteExpand, desc="""\
- `(quasiquote <datum>)`: Data constructed by template instantiation.

  If the datum contains no ``unquote`` expressions, ``quasiquote`` is
  the same as ``quote``.  Otherwise, the unquoted expressions are
  evaluated and their results spliced in.  This is particularly useful
  for constructing model program fragments -- so much so, that the
  modeling inference SPs automatically quasiquote their model
  arguments.

  TODO: Nested quasiquotation does not work properly: all unquoted
  expressions are evaluated regardless of quasiquotation level.

 """)

assumeMacro = quasiquotation_macro("assume", min_size = 3, max_size = 4, desc="""\
- `(assume <symbol> <model-expression> [<label>])`: Programmatically add an assumption.

  Extend the underlying model by adding a new generative random
  variable, like the ``assume`` directive.  The given model expression
  may be constructed programmatically -- see ``unquote``.

  The <label>, if supplied, may be used to ``freeze`` or ``forget``
  this directive.
""")

for m in [identityMacro, lambdaMacro, ifMacro, andMacro, orMacro, letMacro, doMacro, qqMacro,
          assumeMacro,
          ListMacro(), LiteralMacro()]:
  register_macro(m)
