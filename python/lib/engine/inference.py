# Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

from collections import OrderedDict
from copy import copy
import time

from pandas import DataFrame

from venture.engine.plot_spec import PlotSpec
from venture.lite.exception import VentureCallbackError
from venture.lite.exception import VentureValueError
from venture.lite.sp_help import deterministic_typed
from venture.lite.types import ExpressionType
from venture.lite.types import SymbolType
from venture.lite.utils import log_domain_even_out
from venture.lite.utils import logWeightsToNormalizedDirect
from venture.lite.value import VentureArray
from venture.lite.value import VentureInteger
from venture.lite.value import VentureNil
from venture.lite.value import VentureString
from venture.lite.value import VentureSymbol
from venture.lite.value import VentureValue
from venture.ripl.utils import strip_types_from_dict_values
import venture.lite.inference_sps as inf
import venture.lite.types as t
import venture.lite.value as v

class Infer(object):
  def __init__(self, engine):
    self.engine = engine

  @staticmethod
  def _canonicalize(fn):
    if isinstance(fn, VentureString):
      return fn.getString()
    else:
      return fn

  @staticmethod
  def _canonicalize_tree(thing):
    if isinstance(thing, basestring):
      return thing
    elif isinstance(thing, VentureString):
      return thing.getString()
    elif isinstance(thing, list):
      return [Infer._canonicalize_tree(t) for t in thing]

  @staticmethod
  def _format_filenames(filenames,spec):
    if isinstance(filenames, basestring) or \
       isinstance(filenames, VentureString):
      if isinstance(filenames, VentureString):
        filenames = filenames.getString()
      if isinstance(spec, basestring) or isinstance(spec, VentureString):
        return [filenames + '.png']
      else:
        raise VentureValueError(
          'The number of specs must match the number of filenames.')
    else:
      if isinstance(spec, list) and len(spec) == len(filenames):
        return [Infer._canonicalize(filename) + '.png' for filename in filenames]
      else:
        raise VentureValueError(
          'The number of specs must match the number of filenames.')

  def default_name_for_exp(self,exp):
    if isinstance(exp, basestring):
      return exp
    elif hasattr(exp, "__iter__"):
      return "(" + ' '.join([self.default_name_for_exp(e) for e in exp]) + ")"
    else:
      return str(exp)

  def default_names_from_exprs(self, exprs):
    return [self.default_name_for_exp(ExpressionType().asPython(e))
            for e in exprs]

  def parse_exprs(self, exprs, command):
    names = []
    stack_dicts = []
    for expr in exprs:
      name, stack_dict = self.parse_expr(expr, command)
      names.append(name)
      stack_dicts.append(stack_dict)
    return names, stack_dicts

  def parse_expr(self, expr, command):
    special_names = [VentureSymbol(x) for x in ['iter', 'time', 'score']]
    if (isinstance(expr, VentureArray) and
        expr.lookup(VentureInteger(0)) == VentureSymbol('labelled')):
      # The first element is the command, the second is the label for
      # the command
      stack_dict = expr.lookup(VentureInteger(1)).asStackDict()
      name = expr.lookup(VentureInteger(2)).symbol
    elif command == 'printf' and expr in special_names:
      name = expr.getSymbol()
      stack_dict = None
    else:
      # Generate the default name, get the stack dict
      stack_dict = expr.asStackDict()
      name = self.default_name_for_exp(ExpressionType().asPython(expr))
    return name, stack_dict

  def convert_none(self, item):
    if item is None:
      return VentureNil()
    else:
      return item

  def primitive_infer(self, exp): return self.engine.primitive_infer(exp)

  def resample(self, ct): self.engine.resample(ct, 'sequential')
  def resample_serializing(self, ct): self.engine.resample(ct, 'serializing')
  def resample_threaded(self, ct): self.engine.resample(ct, 'threaded')
  def resample_thread_ser(self, ct): self.engine.resample(ct, 'thread_ser')
  def resample_multiprocess(self, ct, process_cap = None):
    self.engine.resample(ct, 'multiprocess', process_cap)

  def likelihood_weight(self): self.engine.likelihood_weight()
  def log_likelihood_at(self, scope, block):
    return self.engine.model.traces.map('log_likelihood_at', scope, block)
  def log_joint_at(self, scope, block):
    return self.engine.model.traces.map('log_joint_at', scope, block)

  def enumerative_diversify(self, scope, block):
    self.engine.diversify(["enumerative", scope, block])
  def collapse_equal(self, scope, block): self.engine.collapse(scope, block)
  def collapse_equal_map(self, scope, block):
    self.engine.collapse_map(scope, block)

  def checkInvariants(self):
    self.engine.model.traces.map('checkInvariants')

  def incorporate(self): self.engine.incorporate()

  def printf(self, dataset): print dataset.asPandas()
  def plotf(self, spec, dataset):
    spec = ExpressionType().asPython(spec)
    spec = self._canonicalize_tree(spec)
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names)
  def plotf_to_file(self, basenames, spec, dataset):
    filenames = ExpressionType().asPython(basenames)
    spec = ExpressionType().asPython(spec)
    spec = self._canonicalize_tree(spec)
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names,
                        self._format_filenames(filenames, spec))
  def sweep(self, dataset):
    print 'Iteration count: ' + str(dataset.asPandas()['iter'].values[-1])

  def call_back(self, name, *exprs):
    name = SymbolType().asPython(name)
    if name not in self.engine.callbacks:
      raise VentureValueError("Unregistered callback {}".format(name))
    args = [self.engine.sample_all(e.asStackDict()) for e in exprs]
    try:
      ans = self.engine.callbacks[name](self, *args)
    except Exception as e:
      import sys
      info = sys.exc_info()
      raise VentureCallbackError(e), None, info[2]
    return self.convert_none(ans)

  def collect(self, *exprs):
    names, stack_dicts = self.parse_exprs(exprs, None)
    answer = OrderedDict() # Map from column name to list of values; the values
                           # are parallel to the particles
    std_names = ['iter', 'prt. id', 'time (s)',
                 'prt. log wgt.', 'prt. prob.']
    def collect_std_streams(engine):
      the_time = time.time() - engine.creation_time
      answer['iter'] = [1] * engine.num_traces()
      answer['prt. id'] = range(engine.num_traces())
      answer['time (s)'] = [the_time] * engine.num_traces()
      log_weights = copy(engine.model.log_weights)
      answer['prt. log wgt.'] = log_weights
      answer['prt. prob.'] = logWeightsToNormalizedDirect(log_weights)
    collect_std_streams(self.engine)
    for name, stack_dict in zip(names, stack_dicts):
      if stack_dict is not None:
        answer[name] = self.engine.sample_all(stack_dict)
    return Dataset(names, std_names, answer)

  def assume(self, sym, exp):
    self.engine.assume(SymbolType().asPython(sym), exp.asStackDict())
  def observe(self, exp, val):
    self.engine.observe(exp.asStackDict(), val.asStackDict())
  def force(self, exp, val):
    self.engine.force(exp.asStackDict(), val.asStackDict())
  def predict(self, exp):
    self.engine.predict(exp.asStackDict())
  def sample(self, exp):
    return VentureValue.fromStackDict(self.engine.sample(exp.asStackDict()))
  def sample_all(self, exp):
    return [VentureValue.fromStackDict(val)
            for val in self.engine.sample_all(exp.asStackDict())]
  def extract_stats(self, exp):
    sp_dict = self.engine.sample(exp.asStackDict())
    return VentureValue.fromStackDict(sp_dict["aux"])
  def load_plugin(self, name, *args):
    return self.convert_none(self.engine.ripl.load_plugin(name, *args))

  def particle_log_weights(self):
    return self.engine.model.log_weights
  def equalize_particle_log_weights(self):
    old = self.engine.model.log_weights
    self.engine.model.log_weights = log_domain_even_out(old)
    return old
  def set_particle_log_weights(self, new_weights):
    assert len(new_weights) == len(self.engine.model.log_weights), \
      "set_particle_log_weights got %d weights, but there are %d particles"
    self.engine.model.log_weights = new_weights
  def particle_normalized_probs(self):
    return logWeightsToNormalizedDirect(self.particle_log_weights())

  def for_each_particle(self, action):
    return self.engine.for_each_particle(action)
  def on_particle(self, index, action):
    return self.engine.on_particle(index, action)

  def convert_model(self, backend_name):
    import venture.shortcuts as s
    backend = s.backend(backend_name)
    self.engine.convert(backend)
  def new_model(self, backend_name=None):
    if backend_name is None:
      backend = None
    else:
      import venture.shortcuts as s
      backend = s.backend(backend_name)
    return self.engine.new_model(backend)
  def fork_model(self, backend_name=None):
    model = self.new_model(backend_name)
    model.convertFrom(self.engine.model)
    return model
  def in_model(self, model, action):
    return self.engine.in_model(model, action)
  def model_import_foreign(self, name):
    return self.engine.import_foreign(name)

  def save_model(self, filename):
    # Go through the ripl because serialize includes extra ripl-level stuff.
    # TODO This does not work with in_model because of
    # https://github.com/probcomp/Venturecxx/issues/338
    self.engine.ripl.save(filename)
  def load_model(self, filename):
    self.engine.ripl.load(filename)

  def select(self, scope, block):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom subproblems only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'select', scope, block)
  def detach(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_detach', scaffold)
  def regen(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_regen', scaffold)
  def restore(self, scaffold, rhoDB):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_restore', scaffold, rhoDB)
  def detach_for_proposal(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'detach_for_proposal', scaffold)
  def regen_with_proposal(self, scaffold, values):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(
      0, 'regen_with_proposal', scaffold, values)
  def get_current_values(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, \
      "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'get_current_values', scaffold)
  def num_blocks(self, scope):
    return self.engine.model.traces.map('numBlocksInScope', scope)

  def pyexec(self, code):
    self.engine.ripl.pyexec(code)
  def pyeval(self, code):
    return self.engine.ripl.pyeval(code)

class Dataset(object):
  """Basically a wrapper for a Pandas Dataframe that knows about a few
special columns (like the iteration count).  If you are a Venture user and
find yourself dealing with one of these, you probably want the
asPandas() method.

  """

  def __init__(self, ind_names=None, std_names=None, data=None):
    self.ind_names = ind_names # :: [String]
    self.std_names = std_names # :: [String]
    self.data = data   # :: {String, [value]}
    # The keys of data are the strings that appear in ind_names and std_names
    # The values of data are all parallel (by particle)
    # Column indexing is resolved by position in ind_names (hence the name)

  def merge(self, other):
    """Functional merge of two datasets.  Returns a newly allocated
Dataset which is the result of the merge. """
    if self.ind_names is None:
      return other
    if other.ind_names is None:
      return self
    self._check_compat(other)
    answer = OrderedDict()
    for (key, vals) in self.data.iteritems():
      if key == "iter" and len(vals) > 0:
        nxt = max(vals)
        answer[key] = vals + [v + nxt for v in other.data[key]]
      else:
        answer[key] = vals + other.data[key]
    return Dataset(self.ind_names, self.std_names, answer)

  def merge_bang(self, other):
    """Imperative merge of two datasets.  Returns self after merging other
into it."""
    if other.ind_names is None:
      return self
    if self.ind_names is None:
      self.ind_names = other.ind_names
      self.std_names = other.std_names
      self.data = OrderedDict([name, []] for name in self.ind_names + self.std_names)
    self._check_compat(other)
    for key in self.data.keys():
      if key == "iter" and len(self.data[key]) > 0:
        nxt = max(self.data[key])
        self.data[key].extend([v + nxt for v in other.data[key]])
      else:
        self.data[key].extend(other.data[key])
    return self

  def _check_compat(self, other):
    if self.ind_names != other.ind_names:
      raise Exception("Cannot merge datasets with different contents %s %s"
                      % (self.ind_names, other.ind_names))
    if self.std_names != other.std_names:
      raise Exception("Cannot merge datasets with different contents %s %s"
                      % (self.std_names, other.std_names))

  def asPandas(self):
    """Return a freshly allocated Pandas DataFrame containing the data in
this Dataset."""
    ds = DataFrame.from_dict(strip_types_from_dict_values(self.data))
    order = self.std_names + self.ind_names
    return ds[order]

# Design rationales for collect and the Dataset object
#
# Problem: How to define general merging of datasets?
# - Cop out: require them to have identical specifications (including
#   column order) for now.
#
# Problem: plotf specifications refer to fields to be plotted by index
# in the data set specification.
# - The merging cop out actually makes this a non-issue, because the
#   columns can be stored by index also.
#
# Alternative considered: store the to be sampled expressions on the
# data set, and have an "extend" operation that samples them again
# without accepting new ones.  Rejected because not clear how this
# would generalize to collecting inference values; maybe revisit when
# that happens.
# - Maybe just accept the macrology.
#
# Problem: It may be nice to be able to add columns to a dataset
# dynamically, but the current merging story doesn't support that.
# Solution: Defer.  For now, just merge on rows, holding columns
# fixed.


def print_fun(*args):
  def convert_arg(arg):
    if isinstance(arg, v.VentureForeignBlob) and \
       isinstance(arg.getForeignBlob(), Dataset):
      return arg.getForeignBlob().asPandas()
    else:
      return arg
  if len(args) == 1:
    print convert_arg(args[0])
  else:
    print [convert_arg(a) for a in args]

def plot_fun(spec, dataset):
  spec = t.ExpressionType().asPython(spec)
  if isinstance(dataset, Dataset):
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names)
  else:
    # Assume a raw data frame
    PlotSpec(spec).plot(dataset, list(dataset.columns.values))

def plot_to_file_fun(basenames, spec, dataset):
  filenames = t.ExpressionType().asPython(basenames)
  spec = t.ExpressionType().asPython(spec)
  if isinstance(dataset, Dataset):
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names,
                        _format_filenames(filenames, spec))
  else:
    PlotSpec(spec).plot(dataset, list(dataset.columns.values),
                        _format_filenames(filenames, spec))

def _format_filenames(filenames,spec):
  if isinstance(filenames, basestring) or isinstance(filenames, v.VentureString):
    if isinstance(filenames, v.VentureString):
      filenames = filenames.getString()
    if isinstance(spec, basestring) or isinstance(spec, v.VentureString):
      return [filenames + '.png']
    else:
      raise VentureValueError('The number of specs must match the number of filenames.')
  else:
    if isinstance(spec, list) and len(spec) == len(filenames):
      return [filename + '.png' for filename in filenames]
    else:
      raise VentureValueError('The number of specs must match the number of filenames.')

inf.registerBuiltinInferenceSP("print", deterministic_typed(print_fun, [t.AnyType()], t.NilType(), variadic=True, descr="""\
Print the given values to the terminal.
"""))

inf.registerBuiltinInferenceSP("plot", deterministic_typed(plot_fun, [t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")], t.NilType(), descr="""\
Plot a data set according to a plot specification.

Example::

    define d = empty()
    assume x = normal(0, 1)
    infer accumulate_dataset(1000,
              do(mh(default, one, 1),
                 collect(x)))
    plot("c0s", d)

will do 1000 iterations of `mh` collecting some standard data and
the value of ``x``, and then show a plot of the ``x`` variable (which
should be a scalar) against the iteration number (from 1 to 1000),
colored according to the global log score.  See `collect`
for details on collecting and labeling data to be plotted.

The format specifications are inspired loosely by the classic
printf.  To wit, each individual plot that appears on a page is
specified by some line noise consisting of format characters
matching the following regex::

    [<geom>]*(<stream>?<scale>?){1,3}

specifying

- the geometric objects to draw the plot with, and
- for each dimension (x, y, and color, respectively)
    - the data stream to use
    - the scale

The possible geometric objects are:

- _p_oint,
- _l_ine,
- _b_ar, and
- _h_istogram

The possible data streams are:

- _<an integer>_ that column in the data set, 0-indexed,
- _%_ the next column after the last used one
- iteration _c_ounter,
- _t_ime (wall clock, since the beginning of the Venture program), and
- pa_r_ticle

The possible scales are:

- _d_irect, and
- _l_ogarithmic

If one stream is indicated for a 2-D plot (points or lines), the x
axis is filled in with the iteration counter.  If three streams are
indicated, the third is mapped to color.

If the given specification is a list, make all those plots at once.
"""))

inf.registerBuiltinInferenceSP("plotf", inf.engine_method_sp("plotf", inf.infer_action_maker_type([t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")]), desc="""\
Plot a data set according to a plot specification.

This is identical to `plot`, except it's an inference action,
so can participate in `do` blocks.

Example::

    do(assume x, normal(0, 1),
       ...
       plotf("c0s", d))
""")[0])

inf.registerBuiltinInferenceSP("plot_to_file", deterministic_typed(plot_to_file_fun, [t.AnyType("<basename>"), t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")], t.NilType(), descr="""\
Save plot(s) to file(s).

Like `plot`, but save the resulting plot(s) instead of displaying on screen.
Just as ``<spec>`` may be either a single expression or a list, ``<basenames>`` may
either be a single symbol or a list of symbols. The number of basenames must
be the same as the number of specifications.

Examples:
  plot_to_file("basename", "spec", <expression> ...) saves the plot specified by
    the spec in the file "basename.png"
  plot_to_file(quote(basename1, basename2), (quote(spec1, spec2)), <expression> ...) saves
    the spec1 plot in the file basename1.png, and the spec2 plot in basename2.png.
"""))

inf.registerBuiltinInferenceSP("plotf_to_file", inf.engine_method_sp("plotf_to_file", inf.infer_action_maker_type([t.AnyType("<basename>"), t.AnyType("<spec>"), t.ForeignBlobType("<dataset>")]), desc="""\
Save plot(s) to file(s).

Like `plotf`, but save the resulting plot(s) instead of displaying on screen.
See `plot_to_file`.
""")[0])

inf.registerBuiltinInferenceSP("empty", deterministic_typed(lambda *args: Dataset(), [], t.ForeignBlobType("<dataset>"), descr="""\
Create an empty dataset `into` which further `collect` ed stuff may be merged.
  """))

inf.registerBuiltinInferenceSP("into", inf.sequenced_sp(lambda orig, new: orig.merge_bang(new), inf.infer_action_maker_type([t.ForeignBlobType(), t.ForeignBlobType()]), desc="""\
Destructively merge the contents of the second argument into the
first.

Right now only implemented on datasets created by `empty` and
`collect`, but in principle generalizable to any monoid.  """))

inf.registerBuiltinInferenceSP("_collect", inf.macro_helper("collect", inf.infer_action_maker_type([t.AnyType()], return_type=t.ForeignBlobType("<dataset>"), variadic=True))[0])

inf.registerBuiltinInferenceSP("printf", inf.engine_method_sp("printf", inf.infer_action_maker_type([t.ForeignBlobType("<dataset>")]), desc="""\
Print model values collected in a dataset.

This is a basic debugging facility.""")[0])

inf.registerBuiltinInferenceSP("sweep", inf.engine_method_sp("sweep", inf.infer_action_maker_type([t.ForeignBlobType("<dataset>")]), desc="""\
Print the iteration count.

Extracts the last row of the supplied inference Dataset and prints its iteration count.
""")[0])
