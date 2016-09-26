# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# Macros that resyntax errors.
# For a description of the framework, see macro_system.py

import random

from venture.exception import VentureException
from venture.sivm.macro_system import Macro
from venture.sivm.macro_system import Syntax
from venture.sivm.macro_system import expand
from venture.sivm.macro_system import getSym
from venture.sivm.macro_system import register_macro
from venture.sivm.pattern_language import SyntaxRule
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
    return isinstance(exp, list) or v.is_basic_val_of_type("array", exp)
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

def CondExpand(exp):
  n = len(exp) - 1
  preds = ['__pred%d__' % i for i in range(n)]
  exprs = ['__expr%d__' % i for i in range(n)]

  pattern = ['cond'] + map(list, zip(preds, exprs))

  template = 'nil'
  for i in reversed(range(n)):
    template = ['if', preds[i], exprs[i], template]
  return SyntaxRule(pattern, template).expand(exp)

def LetExpand(exp):
  if len(exp) != 3:
      raise VentureException('parse',
          '"let" statement requires 2 arguments',expression_index=[])
  if not isinstance(exp[1], list):
      raise VentureException('parse',
          '"let" first argument must be a list',expression_index=[1])

  n = len(exp[1])
  syms = ['__sym%d__' % i for i in range(n)]
  vals = ['__val%d__' % i for i in range(n)]

  pattern = ['let', map(list, zip(syms, vals)), 'body']

  template = 'body'
  for i in reversed(range(n)):
    template = [['lambda', [syms[i]], template], vals[i]]
  return SyntaxRule(pattern, template).expand(exp)

def LetRecExpand(exp):
  if len(exp) != 3:
      raise VentureException('parse',
          '"letrec" statement requires 2 arguments',expression_index=[])
  if not isinstance(exp[1], list):
      raise VentureException('parse',
          '"letrec" first argument must be a list', expression_index=[1])

  n = len(exp[1])
  syms = ['__sym%d__' % i for i in range(n)]
  vals = ['__val%d__' % i for i in range(n)]

  pattern = ['letrec', map(list, zip(syms, vals)), 'body']

  template = ['fix'] + [['quote'] + [syms]] + [['quote'] + [vals]]
  template = ['eval', ['quote', 'body'], template]
  return SyntaxRule(pattern, template).expand(exp)

def ValuesExpand(exp):
  vals = ["__val_%d__" % i for i in range(len(exp)-1)]
  pattern = ["values_list"] + vals
  template = ["list"] + [["ref", val] for val in vals]
  return SyntaxRule(pattern, template).expand(exp)

def arg0(name):
  def applies(exp):
    return isinstance(exp, list) and len(exp) > 0 and getSym(exp[0]) == name
  return applies

def Assume_valuesExpand(exp):
  if len(exp[1])==1: # base case
    pattern = ["assume_values", ["datum-1"], "datum-2"]
    template = ["_assume",
                ["quasiquote", "datum-1"],
                ["quasiquote",["deref",["first","datum-2"]]]]
  else:
    names = exp[1]
    name_vars = ["name_%d" % i for i in range(len(names))]
    lst_name = "__lst_%d__" % random.randint(10000, 99999)
    pattern = ["assume_values", name_vars, "lst_exp"]
    name_exps = [["assume", name, ["deref", ["lookup", lst_name, v.integer(i)]]]
                 for (i, name) in enumerate(names)]
    template = ["do", ["assume", lst_name, "lst_exp"]] + name_exps
  return SyntaxRule(pattern, template).expand(exp)

def DoExpand(exp):
  if len(exp) == 2:
    # One statement
    pattern = ["do", "stmt"]
    template = "stmt"
  else:
    (_do, statement, rest) = (exp[0], exp[1], exp[2:])
    rest_vars = ["rest_%d" % i for i in range(len(rest))]
    if (type(statement) is list and len(statement) == 3 and
        v.basic_val_of_type_content("symbol", statement[1]) == "<-"):
      # Binding statement, regular form
      pattern = ["do", ["var", "<-", "expr"]] + rest_vars
      template = ["bind", "expr", ["lambda", ["var"], ["do"] + rest_vars]]
    elif (type(statement) is list and len(statement) == 3 and
          v.basic_val_of_type_content("symbol", statement[0]) == "<-"):
      # Binding statement, venturescript form
      pattern = ["do", ["<-", "var", "expr"]] + rest_vars
      template = ["bind", "expr", ["lambda", ["var"], ["do"] + rest_vars]]
    elif (type(statement) is list and len(statement) == 3 and
          v.basic_val_of_type_content("symbol", statement[0]) == "let"):
      # Let statement
      pattern = ["do", ["let", "var", "expr"]] + rest_vars
      template = ["let", [["var", "expr"]], ["do"] + rest_vars]
    elif (type(statement) is list and len(statement) == 3 and
          v.basic_val_of_type_content("symbol", statement[0]) == "let_values"):
      # Let_values statement
      n = len(statement[1])
      lst_name = "__lst_%d__" % random.randint(10000, 99999)
      let_vars = ["var_%d" % i for i in range(n)]
      let_exps = [[var, ["deref", ["lookup", lst_name, v.integer(i)]]]
                   for (i, var) in enumerate(let_vars)]
      pattern = ["do", ["let_values", let_vars, "lst_expr"]] + rest_vars
      template = ["let", [[lst_name, "lst_expr"]] + let_exps,
                  ["do"] + rest_vars]
    elif (type(statement) is list and len(statement) == 3 and
          v.basic_val_of_type_content("symbol", statement[0]) == "letrec"):
      # Letrec statement
      mutrec = 0
      for next_statement in rest:
        if (type(next_statement) is list and len(next_statement) == 3 and
          v.basic_val_of_type_content("symbol", next_statement[0]) == "mutrec"):
          mutrec += 1
        else:
          break
      mutrec_vars = [["var_%d" % i, "expr_%d" % i] for i in range(mutrec)]
      pattern = (["do", ["letrec", "var", "expr"]] +
                 [["mutrec"] + e for e in mutrec_vars] +
                 rest_vars[mutrec:])
      template = ["letrec", [["var", "expr"]] + mutrec_vars, ["do"] + rest_vars[mutrec:]]
    else:
      # Non-binding statement
      pattern = ["do", "stmt"] + rest_vars
      template = ["bind_", "stmt", ["lambda", [], ["do"] + rest_vars]]
  return SyntaxRule(pattern, template).expand(exp)

def BeginExpand(exp):
  pattern = ["begin"] + ["form-%d" % form for form in range(len(exp)-1)]
  template = ["do"] + ["form-%d" % form for form in range(len(exp)-1)]
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
    """Gives the macroexpansion of this (sub-)expression as a 3-tuple (pattern, template, bool).

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
  return Macro(arg0(name), expander, desc=desc, intended_for_inference=True)

def ObserveExpand(program):
  assert len(program) == 3 or len(program) == 4
  if len(program) == 4:
    # A label was supplied
    pattern = ["observe", "exp", "val", "label"]
    template = ["_observe", ["quasiquote", "exp"], "val",
                ["quasiquote", "label"]]
  else:
    pattern = ["observe", "exp", "val"]
    template = ["_observe", ["quasiquote", "exp"], "val"]
  return SyntaxRule(pattern, template).expand(program)

identityMacro = SyntaxRule(['identity', 'exp'], 'exp')
lambdaMacro = SyntaxRule(['lambda', 'args', 'body'],
                         ['make_csp', ['quote', 'args'], ['quote', 'body']],
                         desc="""\
.. _proc:
.. object:: proc(<param>, ...) { <body> }

  Construct a procedure.

  The formal parameters must be VentureScript symbols.
  The body must be a VentureScript expression.
  The semantics are like `function` in JavaScript -- produces
  an anonymous function that may read its lexical environment.

  Creation of variable arity procedures is not yet supported.
""")

ifMacro = SyntaxRule(['if', 'predicate', 'consequent', 'alternative'],
                     [['biplex', 'predicate', ['lambda', [], 'consequent'],
                       ['lambda', [], 'alternative']]],
                     desc="""\
.. _if:
.. object:: if (<predicate>) { <consequent> } else { <alternate> }

  Branch control.

  The predicate, consequent, and alternate must be VentureScript expressions.
""")

# Cond is not directly a SyntaxRule because the pattern language does
# not support repetition.  Instead, expansion of a cond form computes a
# ground pattern and template pair of the right size and dynamically
# forms and uses a SyntaxRule out of that.
condMacro = Macro(arg0("cond"), CondExpand, desc="""\
.. _cond:
.. object:: (cond (<predicate> <expression>) ...)

  Multiple branching.

  Each predicate and each expression must be a VentureScript expression.
  If none of the predicates match, returns nil.
  The above is the parsed form; no special concrete syntax for `cond`
  is provided.
""")

andMacro = SyntaxRule(['and', 'exp1', 'exp2'],
                      ['if', 'exp1', 'exp2', v.boolean(False)],
                      desc="""\
.. function:: and(<exp1>, <exp2>)

  Short-circuiting and.
""")

orMacro = SyntaxRule(['or', 'exp1', 'exp2'],
                     ['if', 'exp1', v.boolean(True), 'exp2'],
                     desc="""\
.. function:: or(<exp1>, <exp2>)

  Short-circuiting or.
""")

# Let is not directly a SyntaxRule because the pattern language does
# not support repetition.  Instead, expansion of a let form computes a
# ground pattern and template pair of the right size and dynamically
# forms and uses a SyntaxRule out of that.
letMacro = Macro(arg0("let"), LetExpand, desc="""\
.. _let:
.. object:: (let ((<param> <exp>) ...) <body>)

  Evaluation with local scope.

  Each parameter must be a VentureScript symbol.
  Each exp must be a VentureScript expression.
  The body must be a VentureScript expression.
  The semantics are as JavaScript's variable declaration and Scheme's `let*`:
  each `exp` is evaluated in turn, its result is bound to the `param`,
  and made available to subsequent `exp` s and the `body`.

  The concrete syntax is::

      <param> = <exp>;
      ...
      <body>

""")

# Letrec is not directly a SyntaxRule because the pattern language does
# not support repetition.  Instead, expansion of a let form computes a
# ground pattern and template pair of the right size and dynamically
# forms and uses a SyntaxRule out of that.
letrecMacro = Macro(arg0("letrec"), LetRecExpand, desc="""\
.. _letrec:
.. object:: (letrec ((<param> <exp>) ...) <body>)

  Evaluation with local scope.

  Each parameter must be a VentureScript symbol.
  Each exp must be a VentureScript expression that evaluates to a procedure.
  The body must be a VentureScript expression.
  The semantics are as Scheme's `letrec` (TODO).
  This is useful for defining locally-scoped mutually recursive procedures.

  No concrete syntax is provided (yet).
""")

valuesMacro = Macro(arg0("values_list"), ValuesExpand, desc="""\
.. _values:
.. object:: values_list(<exp>, <exp>, ...)

  Returns a list of references (see `ref`) corresponding to the
  results of evaluating each of its arguments.
  """)

# Do is not directly a SyntaxRule because the pattern language does
# not support repetition or alternatives.  Instead, expansion of a do
# form computes a ground pattern and template pair of the right shape
# and size and dynamically forms and uses a SyntaxRule out of that.
doMacro = Macro(arg0("do"), DoExpand, desc="""\
.. _do:
.. object:: (do <stmt> <stmt> ...)

  Sequence actions that may return results.

  Note: The above template is abstract syntax.  `do` is what
  curly-delimited blocks expand to.

  Each <stmt> except the last may be

    - an action, in which case it is performed and any value it returns
      is dropped, or

    - a binder of the form ``(<variable> <- <action>)`` in which case the
      action is performed and its value is made available to the remainder
      of the `do` form by being bound to the variable, or

    - a let binder of the form ``(let <variable> <expression>)`` in which
      case the value of the expression is just bound to the variable (without
      performing any actions), or

    - a multivalue binder of the form ``(let_values (<var1> <var2> ...) <expression>)``
      in which case the expression is expected to return a list of `ref` s,
      whose values are unpacked into the variables, or

    - a letrec or mutrec binder of the form ``(letrec <var> <exp>)`` or ``(mutrec <var> <exp>)``.
      All mutrec binders headed by a single letrec form a block, which functions
      like letrec in scheme, with the rest of the `do` expression as its body.

  The last <stmt> may not be a binder and must be an action.  The whole
  `do` expression is then a single compound heterogeneous action,
  whose value is the value returned by the last <stmt>.

  If you need an action that produces a value without doing anything, use
  ``return(<value>)`` (see `return`).  If you need an action that
  evaluates an expression and returns its value, use ``action(<exp>)``
  (see `action`).  If you need an action that does nothing and produces
  no useful value, you can use `pass`.

  For example, to make a kernel that does inference until some variable
  in the model becomes "true" (why would anyone want to do that?), you
  can write::

      1 define my_strange_kernel = proc () {
      2   do(finish <- sample(something_from_the_model),
      3      if (finish) {
      4         pass
      5      } else {
      6         do(default_markov_chain(1),
      7            my_strange_kernel())
      8      })}

  Line 2 is a binder for the `do`, which makes
  ``finish`` a variable usable by the remainder of the procedure.  The
  `if` starting on line 3 is an action, and is the last statement of
  the outer `do`.  Line 6 is a non-binder statement for the inner
  `do`.

  The nomenclature is borrowed from the (in)famous ``do`` notation of
  Haskell.  If this helps you think about it, Venture's ``do`` is
  exactly Haskell ``do``, except there is only one monad, which is
  essentially ``State ModelHistory``.  Randomness and actual i/o are not
  treated monadically, but just executed, which we can get away with
  because VentureScript is strict and doesn't aspire to complete functional
  purity.
""", intended_for_inference=True)

beginMacro = Macro(arg0("begin"), BeginExpand, desc="""\
.. function:: begin(<kernel>, ...)

  Perform the given kernels in sequence.
""", intended_for_inference=True)

actionMacro = SyntaxRule(['action', 'exp'],
                         ['do', 'pass', ['return', 'exp']],
                         desc="""\
.. function:: action(<exp>)

  Wrap an object, usually a non-inference function like plotf,
  as an inference action, so it can be used inside a do(...) block.

  The difference between `action` and `return` is that `action` defers
  evaluation of its argument until the action is performed, whereas
  `return` evaluates its argument eagerly.

""", intended_for_inference=True)

qqMacro = Macro(arg0("quasiquote"), QuasiquoteExpand, desc="""\
.. function:: quasiquote(<datum>)

  Data constructed by template instantiation.

  If the datum contains no `unquote` expressions, `quasiquote` is
  the same as `quote`.  Otherwise, the unquoted expressions are
  evaluated and their results spliced in.  This is particularly useful
  for constructing model program fragments in inference programs -- so
  much so, that the modeling inference SPs automatically quasiquote
  their model arguments.

  TODO: Nested quasiquotation does not work properly: all unquoted
  expressions are evaluated regardless of quasiquotation level.

 """)

callBackMacro = quasiquotation_macro("call_back", min_size = 2, desc="""\
.. function:: call_back(<name>, <model-expression>, ...)

  Invoke a user-defined callback.

  Locate the callback registered under the name ``name`` and invoke it with

  - First, the `Infer` instance in which the present inference program
    is being run

  - Then, for each expression in the `call_back` form, a list of
    values for that expression, represented as stack dicts, sampled
    across all extant particles.  The lists are parallel to each
    other.

  Return the value returned by the callback, or ``Nil`` if the callback
  returned ``None``.

  To bind a callback, call the `bind_callback` method on the `Ripl` object::

      ripl.bind_callback(<name>, <callable>):

      Bind the given Python callable as a callback function that can be
      referred to by `call_back` by the given name (which is a string).

  There is an example in the source in
  ``test/inference_language/test_callback.py``.
""")

collectMacro = quasiquotation_macro("collect", min_size = 2, desc="""\
.. function:: collect(<model-expression> ...)

  Extract data from the underlying model during inference.

  When a `collect` inference command is executed, the given
  expressions are sampled and their values are returned in a
  `Dataset` object.  This is the way to get data into datasets; see
  `accumulate_dataset` and `into` for accumulating datasets,
  and `print`, `plot`, and `plot_to_file` for using them.

  Each ``<model-expression>`` may optionally be given in the form ``labelled(
  <model-expression>, <name>)``, in which case the given ``name`` serves as the
  key in the returned table of data.  Otherwise, the key defaults
  to a string representation of the given ``expression``.

  *Note:* The ``<model-expression>`` s are sampled in the *model*, not the
  inference program.  For example, they may refer to variables
  `assume` d in the model, but may not refer to variables `define` d
  in the inference program.  The ``<model-expression>`` s may be constructed
  programmatically: see `unquote`.

  `collect` also automatically collects some standard items: the
  iteration count (maintained by merging datasets), the particle id, the
  wall clock time that passed since the VentureScript program began, the
  global log score, the particle weights in log space, and the
  normalized weights of the particles in direct space.

  If you want to do something custom with the data, you will want to
  use the `asPandas()` method of the `Dataset` object from your callback
  or foreign inference sp.
""")

assumeMacro = quasiquotation_macro("assume",
    min_size = 3, max_size = 4, desc="""\
.. _assume:
.. object:: [<label>:] assume <symbol> = <model-expression>;

  Programmatically add an assumption.

  Extend the underlying model by adding a new generative random
  variable, like the `assume` directive.  The given model expression
  may be constructed programmatically -- see `unquote`.

  The ``<label>``, if supplied, may be used to `freeze` or `forget`
  this directive.
""")

assume_valuesMacro = Macro(arg0("assume_values"), Assume_valuesExpand,
    desc="""\
.. _assume_values:
.. object:: assume_values (<symbol> ...) = <model-expression>;

  Multiple-value `assume`.

  The expression is expected to produce a list of references (see
  `ref`) of the same length as the list of symbols given to
  ``assume_values``.  ``assume_values`` binds those symbols to the
  `deref` s of the corresponding references.

  For example::

    (assume_values (a b) (list (ref (normal 0 1)) (ref (normal 1 2))))

  is equivalent to::

    (assume _some_name_432_ (list (ref (normal 0 1)) (ref (normal 1 2))))
    (assume a (deref (first _some_name_432_)))
    (assume b (deref (second _some_name_432_)))

  which has the same effect as::

    (assume a (normal 0 1))
    (assume b (normal 0 1))

  `assume_values` does not accept a custom ``label`` argument.
""", intended_for_inference=True)

observeMacro = Macro(arg0("observe"), ObserveExpand, desc="""\
.. _observe:
.. object:: [<label>:] observe <model-expression> = <value>;

  Programmatically add an observation.

  Condition the underlying model by adding a new observation, like the
  `observe` directive.  The given model expression may be
  constructed programmatically -- see `unquote`.  The given value is
  computed in the inference program, and may be stochastic.  This
  corresponds to conditioning a model on randomly chosen data.

  The ``<label>``, if supplied, may be used to `forget` this observation.

""", intended_for_inference=True)

forceMacro = SyntaxRule(["force", "exp", "val"],
                        ["_force", ["quasiquote", "exp"], "val"],
                        desc="""\
.. _force
.. object:: force <model-expression> = <value>;

  Programatically force the state of the model.

  Force the model to set the requested variable to the given value,
  without constraining it to stay that way. Implemented as an
  `observe` followed by a `forget`.

""", intended_for_inference=True)

predictMacro = quasiquotation_macro("predict",
    min_size = 2, max_size = 3, desc="""\
.. _predict:
.. object:: [<label>:] predict <model-expression>;

  Programmatically add a prediction.

  Extend the underlying model by adding a new generative random
  variable, like the `predict` directive.  The given model expression
  may be constructed programmatically -- see `unquote`.

  The ``<label>``, if supplied, may be used to `freeze` or `forget`
  this directive.
""")

predictAllMacro = quasiquotation_macro("predict_all",
    min_size = 2, max_size = 3, desc="""\
.. function:: predict_all(<model-expression>, [<label>])

  Programmatically add a prediction and return results from all particles.

  Extend the underlying model by adding a new generative random
  variable, `predict`.  Unlike `predict`, return the values of the
  expression from all the particles, as a list.

  The ``<label>``, if supplied, may be used to `freeze` or `forget`
  this directive.
""")

sampleMacro = quasiquotation_macro("sample",
    min_size = 2, max_size = 2, desc="""\
.. _sample:
.. object:: sample <model-expression>

  Programmatically sample from the model.

  Sample an expression from the underlying model by simulating a new
  generative random variable without adding it to the model, like the
  `sample` directive.  If there are multiple particles, refers to
  the distinguished one.

  The given model expression may be constructed programmatically --
  see `unquote`.
""")

sampleAllMacro = quasiquotation_macro("sample_all",
    min_size = 2, max_size = 2, desc="""\
.. function:: sample_all(<model-expression>)

  Programmatically sample from the model in all particles.

  Sample an expression from the underlying model by simulating a new
  generative random variable without adding it to the model, like the
  `sample` directive.

  Unlike the `sample` directive, interacts with all the particles,
  and returns values from all of them as a list.

  The given model expression may be constructed programmatically --
  see `unquote`.
""")

extractStatsMacro = quasiquotation_macro("extract_stats",
    min_size = 2, max_size = 2, desc="""\
.. function:: extract_stats(<model-expression>)

  Extract maintained statistics.

  Specifically, sample the given model expression, like `sample`,
  but expect it to return a stochastic procedure and reify and return
  the statistics about its applications that it has collected.

  The exact VentureScript-level representation of the returned statistics
  depends on the procedure in question.  If the procedure does not
  collect statistics, return ``nil``.

  For example::

    assume coin = make_beta_bernoulli(1, 1)
    observe coin() = true
    extract_stats(coin) --> list(1, 0)

""")

# XXX ref and deref don't need to be macros (Issue #225), but
# rewriting them as definitions is blocked on dealing with the model
# prelude, Issue #213.
refMacro = SyntaxRule(['ref', 'expr'],
                      ['let', [['it', 'expr']],
                       ['make_ref', ['lambda', [], 'it']]],
                      desc="""\
.. function:: ref(<object>)

Create a reference to the given object.

The use of references is that the reference itself is deterministic
even if the object is stochastic, and constraint back-propagates from
dereferencing to the random choice generating the object.  A reference
may therefore be stored in data structures without causing them to
be resampled if the object changes, and without preventing the object
from being observed after being taken out of the data structure.

For example::

    [assume lst (list (ref (normal 0 1)) (ref (normal 0 1)))]
    [observe (deref (first lst)) 3]

""")

derefMacro = SyntaxRule(['deref', 'expr'], [['ref_get', 'expr']],
                        desc="""\
.. function:: deref(<object>)

Dereference a reference created with `ref`.

The use of references is that the reference itself is deterministic
even if the object is stochastic, and constraint back-propagates from
dereferencing to the random choice generating the object.  A reference
may therefore be stored in data structures without causing them to
be resampled if the object changes, and without preventing the object
from being observed after being taken out of the data structure.

For example::

    [assume lst (list (ref (normal 0 1)) (ref (normal 0 1)))]
    [observe (deref (first lst)) 3]

""")

for m in [identityMacro, lambdaMacro, ifMacro, condMacro, andMacro, orMacro,
          letMacro, letrecMacro, valuesMacro,
          doMacro, beginMacro, actionMacro, qqMacro,
          callBackMacro, collectMacro,
          assumeMacro, assume_valuesMacro, observeMacro,
          predictMacro, predictAllMacro, forceMacro,
          sampleMacro, sampleAllMacro,
          extractStatsMacro,
          refMacro, derefMacro,
          ListMacro(), LiteralMacro()]:
  register_macro(m)
