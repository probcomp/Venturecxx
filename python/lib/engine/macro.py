# Inference-program macros.

# Perhaps this should be unified with the modeling language macros
# that are expanded by venture.sivm.macro (first).  One difference:
# this code does not conserve expression indexes the way the sivm
# macro expander does.  This is probably a bug.

import venture.value.dicts as v

def macroexpand_inference(program):
  if type(program) is list and len(program) == 0:
    return program
  elif type(program) is list and type(program[0]) is dict and program[0]["value"] in macros:
    return macros[program[0]["value"]](program)
  elif type(program) is list: return [macroexpand_inference(p) for p in program]
  else: return program

macro_list = []
macros = {}

def register_macro(name, func, desc=None):
  macro_list.append((name, func, desc))
  macros[name] = func

def begin_macro(program):
  assert len(program) >= 2
  return [v.sym("sequence"), [v.sym("list")] + [macroexpand_inference(e) for e in program[1:]]]
register_macro("begin", begin_macro, """\
- `(begin <kernel> ...)`: Perform the given kernels in sequence.
""")

def do_macro(program):
  def bind_statement_var(statement):
    if (type(statement) is list and len(statement) == 3 and type(statement[1]) is dict and
        statement[1]["value"] == "<-"):
      # Regular form
      return statement[0]
    if (type(statement) is list and len(statement) == 3 and type(statement[0]) is dict and
        statement[0]["value"] == "<-"):
      # Venturescript parser produces this
      return statement[1]
    # Not a bind statement
    return None
  if len(program) == 2:
    # Do statement with one statement
    return macroexpand_inference(program[1])
  else:
    assert len(program) > 2
    (do, statement, rest) = (program[0], program[1], program[2:])
    var = bind_statement_var(statement)
    if var:
      # Bind a variable
      assert type(var) is dict and statement[0]["type"] is "symbol" # Only bind variables
      rest_body = [do] + rest
      rest_expanded = [v.sym("make_csp"), v.quote([var]),
                       v.quote(macroexpand_inference(rest_body))]
      return [v.sym("bind"), macroexpand_inference(statement[2]), rest_expanded]
    else:
      # Sequence actions
      rest_body = [do] + rest
      rest_expanded = [v.sym("make_csp"), v.quote([]),
                       v.quote(macroexpand_inference(rest_body))]
      return [v.sym("bind_"), macroexpand_inference(statement), rest_expanded]
register_macro("do", do_macro, """\
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

def cycle_macro(program):
  assert len(program) == 3
  subkernels = macroexpand_inference(program[1])
  transitions = macroexpand_inference(program[2])
  return [program[0], [v.sym("list")] + subkernels, transitions]
register_macro("cycle", cycle_macro, """\
- `(cycle (<kernel> ...) <transitions>)`: Run a cycle kernel.

  Execute each of the given subkernels in order.

  The `transitions` argument specifies how many times to do this.
""")

def mixture_macro(program):
  assert len(program) == 3
  weights = []
  subkernels = []
  weighted_ks = macroexpand_inference(program[1])
  transitions = macroexpand_inference(program[2])
  for i in range(len(weighted_ks)/2):
    j = 2*i
    k = j + 1
    weights.append(weighted_ks[j])
    subkernels.append(weighted_ks[k])
  return [program[0], [v.sym("simplex")] + weights, [v.sym("array")] + subkernels, transitions]
register_macro("mixture", mixture_macro, """\
- `(mixture (<weight> <kernel> ...) <transitions>)`: Run a mixture kernel.

  Choose one of the given subkernels according to its weight and
  execute it.

  The `transitions` argument specifies how many times to do this.
""")

def quasiquotation_macro(min_size = None, max_size = None):
  def the_macro(program):
    if min_size is not None:
      assert len(program) >= min_size
    if max_size is not None:
      assert len(program) <= max_size
    return [program[0]] + [v.quasiquote(e) for e in program[1:]]
  return the_macro

register_macro("call_back", quasiquotation_macro(2), """\
- `(call_back <name> <model-expression> ...)`: Invoke a user-defined callback.

  Locate the callback registered under the name `name` and invoke it with

  - First, the Infer instance in which the present inference program
    is being run

  - Then, for each expression in the call_back form, a list of
    values for that expression, represented as stack dicts, sampled
    across all extant particles.  The lists are parallel to each
    other.

  Return the value returned by the callback, or Nil if the callback
  returned None.

  To bind a callback, call the ``bind_callback`` method on the Ripl object::

      ripl.bind_callback(<name>, <callable>):

      Bind the given Python callable as a callback function that can be
      referred to by `call_back` by the given name (which is a string).

  There is an example in test/inference_language/test_callback.py.
""")

register_macro("collect", quasiquotation_macro(2), """\
- `(collect <model-expression> ...)`: Extract data from the underlying
  model during inference.

  When a `collect` inference command is executed, the given
  expressions are sampled and their values are returned in a
  ``Dataset`` object.  This is the way to get data into datasets; see
  ``into`` for accumulating datasets, and ``printf``, ``plotf``, and
  ``plotf_to_file`` for using them.

  Each <model-expression> may optionally be given in the form (labelled
  <model-expression> <name>), in which case the given `name` serves as the
  key in the returned table of data.  Otherwise, the key defaults
  to a string representation of the given `expression`.

  *Note:* The <model-expression>s are sampled in the _model_, not the
  inference program.  For example, they may refer to variables
  ``assume`` d in the model, but may not refer to variables ``define`` d
  in the inference program.  The <model-expression>s may be constructed
  programmatically: see ``unquote``.

  ``collect`` also automatically collects some standard items: the
  sweep count (maintained by merging datasets), the particle id, the
  wall clock time that passed since the Venture program began, the
  global log score, the particle weights in log space, and the
  normalized weights of the particles in direct space.
""")

register_macro("assume", quasiquotation_macro(3, 4), """\
- `(assume <symbol> <model-expression>)`: Programmatically add an assumption.

  Extend the underlying model by adding a new generative random
  variable, like the ``assume`` directive.  The given model expression
  may be constructed programmatically -- see ``unquote``.

""")

def quasiquote_first_macro(program):
  assert len(program) == 3
  return [program[0], v.quasiquote(program[1]), macroexpand_inference(program[2])]

register_macro("observe", quasiquote_first_macro, """\
- `(observe <model-expression> <value>)`: Programmatically add an observation.

  Condition the underlying model by adding a new observation, like the
  ``observe`` directive.  The given model expression may be
  constructed programmatically -- see ``unquote``.  The given value is
  computed in the inference program, and may be stochastic.  This
  corresponds to conditioning a model on randomly chosen data.

  *Note:* Observations are buffered by Venture, and do not take effect
  immediately.  Call ``incorporate`` when you want them to.
  ``incorporate`` is called automatically before every toplevel
  ``infer`` instruction, but if you are using ``observe`` inside a
  compound inference program, you may not execute another toplevel
  ``infer`` instruction for a while.

""")

register_macro("force", quasiquote_first_macro, """\
- `(force <model-expression> <value>)`: Programatically force the state of the model.

  Force the model to set the requested variable to the given value. Implemented
  as an ``observe`` followed by a ``forget``.

""")

register_macro("predict", quasiquotation_macro(2, 2), """\
- `(predict <model-expression>)`: Programmatically add a prediction.

  Extend the underlying model by adding a new generative random
  variable, like the ``predict`` directive.  The given model expression
  may be constructed programmatically -- see ``unquote``.
""")

register_macro("sample", quasiquotation_macro(2, 2), """\
- `(sample <model-expression>)`: Programmatically sample from the model.

  Sample an expression from the underlying model by simulating a new
  generative random variable without adding it to the model, like the
  ``sample`` directive.  If there are multiple particles, refers to
  the distinguished one.

  The given model expression may be constructed programmatically --
  see ``unquote``.  """)

register_macro("sample_all", quasiquotation_macro(2, 2), """\
- `(sample_all <model-expression>)`: Programmatically sample from the model in all particles.

  Sample an expression from the underlying model by simulating a new
  generative random variable without adding it to the model, like the
  ``sample`` directive.

  Unlike the ``sample`` directive, interacts with all the particles,
  and returns values from all of them as a list.

  The given model expression may be constructed programmatically --
  see ``unquote``.  """)
