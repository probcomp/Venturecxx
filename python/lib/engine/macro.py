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
  if len(program) == 2:
    # Do statement with one statement
    return macroexpand_inference(program[1])
  else:
    assert len(program) > 2
    (do, statement, rest) = (program[0], program[1], program[2:])
    if (type(statement) is list and len(statement) == 3 and type(statement[1]) is dict and
        statement[1]["value"] == "<-"):
      # Bind a variable
      assert type(statement[0]) is dict and statement[0]["type"] is "symbol" # Only bind variables
      rest_body = [do] + rest
      rest_expanded = [v.sym("make_csp"), v.quote([statement[0]]),
                       v.quote(macroexpand_inference(rest_body))]
      return [v.sym("bind"), macroexpand_inference(statement[2]), rest_expanded]
    else:
      # Sequence actions
      rest_body = [do] + rest
      return [v.sym("bind_"), macroexpand_inference(statement), macroexpand_inference(rest_body)]
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

register_macro("peek", quasiquotation_macro(2), """\
- `(peek <model-expression> ...)`: Extract data from the underlying
  model during inference.

  Every time a `peek` inference command is executed, the given
  expressions are sampled and their values are stored.  When inference
  completes, the data extracted is either returned, if Venture is
  being used as a library, or printed, if from the interactive
  console.

  Each <model-expression> may optionally be given in the form (labelled
  <model-expression> <name>), in which case the given `name` serves as the
  key in the returned table of peek data.  Otherwise, the key defaults
  to a string representation of the given `expression`.

  *Note:* The <model-expression>s are sampled in the _model_, not the
  inference program.  For example, they may refer to variables
  ``assume`` d in the model, but may not refer to variables ``define`` d
  in the inference program.  The <model-expression>s may be constructed
  programmatically: see ``unquote``.

""")

register_macro("printf", quasiquotation_macro(2), """\
- `(printf <model-expression> ...)`: Print model values.

  Every time a `printf` command is executed, the given model
  expressions are sampled and their values printed to standard output.
  This is a basic debugging facility.

  See the note about model expressions from ``peek``.
""")

register_macro("plotf", quasiquotation_macro(2), """\
- `(plotf <spec> <model-expression> ...)`: Accumulate data for plotting.

  Every time a `plotf` command is executed, the given model expressions are
  sampled and their values are stored.  When inference completes, the
  data extracted is either returned as a ``SpecPlot`` object, if
  Venture is being used as a library, or plotted on the screen, if
  from the interactive console.

  The two most useful methods of the ``SpecPlot`` are ``plot()``,
  which draws that plot on the screen, and ``dataset()``, which
  returns the stored data as a Pandas DataFrame.

  The semantics of the plot specifications are best captured by the
  docstring of the ``SpecSplot`` class, which is embedded here for
  convenience::

      Example:
        [INFER (cycle ((mh default one 1) (plotf c0s x)) 1000)]
      will do 1000 iterations of MH and then show a plot of the x variable
      (which should be a scalar) against the sweep number (from 1 to
      1000), colored according to the global log score.

      Example library use:
        ripl.infer("(cycle ((mh default one 1) (plotf c0s x)) 1000)")
      will return an object representing that same plot that will draw it
      if `print`ed.  The collected dataset can also be extracted from the
      object for more flexible custom plotting.

      The format specifications are inspired loosely by the classic
      printf.  To wit, each individual plot that appears on a page is
      specified by some line noise consisting of format characters
      matching the following regex

      [<geom>]*(<stream>?<scale>?){1,3}

      specifying
      - the geometric objects to draw the plot with
      - for each dimension (x, y, and color, respectively)
        - the data stream to use
        - the scale

      Each requested data stream is sampled once every time the inference
      program executes the plotf instruction, and the plot shows all of
      the samples after inference completes.

      The possible geometric objects are:
        _p_oint, _l_ine, _b_ar, and _h_istogram
      The possible data streams are:
        _<an integer>_ that expression, 0-indexed,
        _%_ the next expression after the last used one
        sweep _c_ounter, _t_ime (wall clock), log _s_core, and pa_r_ticle
      The possible scales are:
        _d_irect, _l_og

      If one stream is indicated for a 2-D plot (points or lines), the x
      axis is filled in with the sweep counter.  If three streams are
      indicated, the third is mapped to color.

      If the given specification is a list, make all those plots at once.

  The expressions can optionally be labelled in the same way as for ``peek``.
  See also the note about them being model expressions there.
""")

register_macro("plotf_to_file", quasiquotation_macro(3), """\
- `(plotf_to_file <basenames> <spec> <model-expression> ...)`: Accumulate data for plotting to files.

  Like ``plotf``, but save the resulting plot(s) instead of displaying on screen.
  Just as <spec> may be either a single expression or a list, <basenames> may
  either be a single symbol or a list of symbols. The number of basenames must
  be the same as the number of specifications.

  Examples:
    (plotf_to_file basename spec <expression> ...) saves the plot specified by
      the spec in the file "basename.png"
    (plotf_to_file (basename1 basename2) (spec1 spec2) <expression> ...) saves
      the spec1 plot in the file basename1.png, and the spec2 plot in basename2.png.
""")

register_macro("call_back", quasiquotation_macro(2), """\
- `(call_back <name> <model-expression> ...)`: Invoke a user-defined callback.

  Locate the callback registered under the name `name` and invoke it with

  - First, the Infer instance in which the present inference program
    is being run

  - Then, for each expression in the call_back form, a list of
    values for that expression, represented as stack dicts, sampled
    across all extant particles.  The lists are parallel to each
    other.

  To bind a callback, call the ``bind_callback`` method on the Ripl object::

      ripl.bind_callback(<name>, <callable>):

      Bind the given Python callable as a callback function that can be
      referred to by `call_back` by the given name (which is a string).

  There is an example in test/inference_language/test_callback.py.
""")

register_macro("call_back_accum", quasiquotation_macro(2), """\
- `(call_back_accum <name> <model-expression> ...)`: Accumulate data for a user-defined callback.

  Like ``call_back``, but accumulates the data during the inference
  program, and calls the callback with a Pandas DataFrame containing
  it once enclosing the ``infer`` instruction completes.

""")

register_macro("assume", quasiquotation_macro(3, 3), """\
- `(assume <symbol> <model-expression>)`: Programmatically add an assumption.

  Extend the underlying model by adding a new generative random
  variable, like the ``assume`` directive.  The given model expression
  may be constructed programmatically -- see ``unquote``.

""")

def observe_macro(program):
  assert len(program) == 3
  return [program[0], v.quasiquote(program[1]), macroexpand_inference(program[2])]
register_macro("observe", observe_macro, """\
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
