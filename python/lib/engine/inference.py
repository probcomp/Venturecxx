# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import time
from pandas import DataFrame, Index
from copy import copy

from venture.lite.value import (ExpressionType, SymbolType, VentureArray, VentureSymbol,
                                VentureInteger, VentureValue, VentureNil)
from venture.lite.utils import logWeightsToNormalizedDirect
from venture.ripl.utils import strip_types_from_dict_values
from venture.lite.exception import VentureValueError
from plot_spec import PlotSpec

class Infer(object):
  # In order to count iterations, can only have one call to each of printf, peek, plotf
  # This will still multi-count interations if you enter the identical printf command multiple times
  # I don't want these methods accessible to other modules, but Infer needs to access them
  # pylint:disable=protected-access
  def __init__(self, engine):
    self.engine = engine
    self.out = {}
    self.result = None

  def final_data(self):
    # add the last data point if result isn't None
    if self.result is not None and not self.result._final_appended:
      self.result._save_previous_iter(self.result.sweep + 1)
      self.result._final_appended = True
    return self.result

  def _init_peek(self, names, exprs, stack_dicts):
    if self.result is None:
      self.result = InferResult(first_command = 'peek')
    if self.result._peek_names is None:
      self.result._init_peek(names, exprs, stack_dicts)
    elif (names == self.result._peek_names and
          exprs == self.result._peek_exprs):
      pass
    else:
      raise VentureValueError("Cannot issue multiple peek commands in the same inference program")

  def _init_print(self, names, exprs, stack_dicts):
    if self.result is None:
      self.result = InferResult(first_command = 'printf')
    if self.result._print_names is None:
      self.result._init_print(names, exprs, stack_dicts)
    elif (names == self.result._print_names and
          exprs == self.result._print_exprs):
      pass
    else:
      raise VentureValueError("Cannot issue multiple printf commands in same inference program")

  def _init_plot(self, spec, names, exprs, stack_dicts, filenames=None, callback=None):
    if self.result is None:
      if filenames is None and callback is None:
        cmd = 'plotf'
      elif filenames is not None and callback is None:
        cmd = 'plotf_to_file'
        filenames = self._format_filenames(filenames, spec)
      elif filenames is None and callback is not None:
        cmd = 'call_back_accum'
      else:
        raise VentureValueError("Accumulating and saving to file not supported at once in Infer._init_plot.")
      self.result = InferResult(first_command = cmd, filenames = filenames, callback = callback)
    if self.result.spec_plot is None:
      self.result._init_plot(spec, names, exprs, stack_dicts)
    elif (spec == self.result.spec_plot.spec_string and
          names == self.result.spec_plot.names and
          exprs == self.result.spec_plot.exprs):
      pass
    else:
      raise VentureValueError("Cannot plot with different specs in the same inference program")

  @staticmethod
  def _format_filenames(filenames,spec):
    if isinstance(filenames, basestring):
      if isinstance(spec, basestring):
        return [filenames + '.png']
      else:
        raise VentureValueError('The number of specs must match the number of filenames.')
    else:
      if isinstance(spec, list) and len(spec) == len(filenames):
        return [filename + '.png' for filename in filenames]
      else:
        raise VentureValueError('The number of specs must match the number of filenames.')

  def default_name_for_exp(self,exp):
    if isinstance(exp, basestring):
      return exp
    elif hasattr(exp, "__iter__"):
      return "(" + ' '.join([self.default_name_for_exp(e) for e in exp]) + ")"
    else:
      return str(exp)

  def default_names_from_exprs(self, exprs):
    return [self.default_name_for_exp(ExpressionType().asPython(e)) for e in exprs]

  def parse_exprs(self, exprs, command):
    names = []
    stack_dicts = []
    for expr in exprs:
      name, stack_dict = self.parse_expr(expr, command)
      names.append(name)
      stack_dicts.append(stack_dict)
    return names, stack_dicts

  def parse_expr(self, expr, command):
    special_names = [VentureSymbol(x) for x in ['sweep', 'time', 'score']]
    if (type(expr) is VentureArray and
        expr.lookup(VentureInteger(0)) == VentureSymbol('labelled')):
      # the first element is the command, the second is the label for the command
      stack_dict = expr.lookup(VentureInteger(1)).asStackDict()
      name = expr.lookup(VentureInteger(2)).symbol
    elif command == 'printf' and expr in special_names:
      name = expr.getSymbol()
      stack_dict = None
    else:
      # generate the default name, get the stack dict
      stack_dict = expr.asStackDict()
      name = self.default_name_for_exp(ExpressionType().asPython(expr))
    return name, stack_dict

  def convert_none(self, item):
    if item is None:
      return VentureNil()
    else:
      return item

  def primitive_infer(self, exp): self.engine.primitive_infer(exp)
  def resample(self, ct): self.engine.resample(ct, 'sequential')
  def resample_serializing(self, ct): self.engine.resample(ct, 'serializing')
  def resample_threaded(self, ct): self.engine.resample(ct, 'threaded')
  def resample_thread_ser(self, ct): self.engine.resample(ct, 'thread_ser')
  def resample_multiprocess(self, ct, process_cap = None): self.engine.resample(ct, 'multiprocess', process_cap)
  def likelihood_weight(self): self.engine.trace_handler.likelihood_weight()
  def likelihood_at(self, scope, block):
    return self.engine.trace_handler.delegate('likelihood_at', scope.getSymbol(), block.getSymbol())
  def posterior_at(self, scope, block):
    return self.engine.trace_handler.delegate('posterior_at', scope.getSymbol(), block.getSymbol())
  def enumerative_diversify(self, scope, block): self.engine.diversify(["enumerative", scope, block])
  def collapse_equal(self, scope, block): self.engine.collapse(scope, block)
  def collapse_equal_map(self, scope, block): self.engine.collapse_map(scope, block)
  def incorporate(self): self.engine.trace_handler.incorporate()
  def peek(self, *exprs):
    names, stack_dicts = self.parse_exprs(exprs, 'peek')
    self._init_peek(names, exprs, stack_dicts)
    self.result._add_data(self.engine, 'peek')
  def printf(self, *exprs):
    names, stack_dicts = self.parse_exprs(exprs, 'printf')
    self._init_print(names, exprs, stack_dicts)
    self.result._add_data(self.engine, 'printf')
    self.result._print_data()
  def plotf(self, spec, *exprs): # This one only works from the "plotf" SP.
    spec = ExpressionType().asPython(spec)
    names, stack_dicts = self.parse_exprs(exprs, 'plotf')
    self._init_plot(spec, names, exprs, stack_dicts)
    self.result._add_data(self.engine, 'plotf')
  def plotf_to_file(self, basenames, spec, *exprs): # This one only works from the "plotf_to_file" SP.
    filenames = ExpressionType().asPython(basenames)
    spec = ExpressionType().asPython(spec)
    names, stack_dicts = self.parse_exprs(exprs, 'plotf')
    self._init_plot(spec, names, exprs, stack_dicts, filenames=filenames)
    self.result._add_data(self.engine, 'plotf_to_file')
  def call_back(self, name, *exprs):
    name = SymbolType().asPython(name)
    if name not in self.engine.callbacks:
      raise VentureValueError("Unregistered callback {}".format(name))
    return self.convert_none(self.engine.callbacks[name](self, *[self.engine.sample_all(e.asStackDict()) for e in exprs]))
  def call_back_accum(self, name, *exprs):
    name = SymbolType().asPython(name)
    if name not in self.engine.callbacks:
      raise VentureValueError("Unregistered callback {}".format(name))
    names, stack_dicts = self.parse_exprs(exprs, 'plotf')
    self._init_plot(None, names, exprs, stack_dicts, callback=self.engine.callbacks[name])
    self.result._add_data(self.engine, 'call_back_accum')
  def collect(self, *exprs):
    names, stack_dicts = self.parse_exprs(exprs, None)
    answer = {} # Map from column name to list of values; the values
                # are parallel to the particles
    std_names = ['sweep count', 'particle id', 'time (s)', 'log score',
                 'particle log weight', 'particle normalized prob']
    def collect_std_streams(engine):
      the_time = time.time() - engine.creation_time
      answer['sweep count'] = [0] * engine.num_traces()
      answer['particle id'] = range(engine.num_traces())
      answer['time (s)'] = [the_time] * engine.num_traces()
      answer['log score'] = engine.logscore_all() # TODO Replace this by explicit references to (global_likelihood), because the current implementation is wrong
      log_weights = copy(engine.trace_handler.log_weights)
      answer['particle log weight'] = log_weights
      answer['particle normalized prob'] = logWeightsToNormalizedDirect(log_weights)
    collect_std_streams(self.engine)
    for name, stack_dict in zip(names, stack_dicts):
      if stack_dict is not None:
        answer[name] = self.engine.sample_all(stack_dict)
    return Dataset(names, std_names, answer)
  def plotf_new(self, spec, dataset):
    spec = ExpressionType().asPython(spec)
    # TODO I hope ind_names is right for the names of the spec plot;
    # not specifying the exprs and stack dicts should be fine.
    plot = SpecPlot(spec, dataset.ind_names, None, None)
    plot.plot(dataset.asPandas())

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
    return [VentureValue.fromStackDict(val) for val in self.engine.sample_all(exp.asStackDict())]
  def load_plugin(self, name, *args):
    return self.convert_none(self.engine.ripl.load_plugin(name, *args))

  def particle_log_weights(self):
    return self.engine.trace_handler.log_weights
  def set_particle_log_weights(self, new_weights):
    assert len(new_weights) == len(self.engine.trace_handler.log_weights)
    self.engine.trace_handler.log_weights = new_weights
  def particle_normalized_probs(self):
    return logWeightsToNormalizedDirect(self.particle_log_weights())

class Dataset(object):
  """Explain to me how exactly this class is different from a Pandas DataFrame?"""
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
    answer = {}
    for (key, vals) in self.data.iteritems():
      answer[key] = vals + other.data[key]
    return Dataset(self.ind_names, self.std_names, answer)

  def merge_bang(self, other):
    "Imperative merge of two datasets.  Returns self after merging other into it."
    if other.ind_names is None:
      return self
    if self.ind_names is None:
      self.ind_names = other.ind_names
      self.std_names = other.std_names
      self.data = dict([name, []] for name in self.ind_names + self.std_names)
    self._check_compat(other)
    for key in self.data.keys():
      self.data[key].extend(other.data[key])
    return self

  def _check_compat(self, other):
    if not self.ind_names == other.ind_names:
      raise Exception("Cannot merge datasets with different contents %s %s" % (self.ind_names, other.ind_names))
    if not self.std_names == other.std_names:
      raise Exception("Cannot merge datasets with different contents %s %s" % (self.std_names, other.std_names))

  def asPandas(self):
    ds = DataFrame.from_dict(strip_types_from_dict_values(self.data))
    order = self.std_names + self.ind_names
    return ds[order]


class InferResult(object):
  '''
  Returned if any of "peek", "plotf", "printf" issued in an "infer" command.
  There may be at most one of each command per inference program.
  Any number of arguments may be given to plotf and peek. Each argument must be
  either a Venture model expression, or a statement of the form
  (labelled <venture-expression> <expression-label>).
  If a model expression is given, the expression is sampled, recorded, and
  printed to the screen in the case of plotf. If a (labelled) statement is
  given, <venture-expression> is the model expression to sample.
  <expression-label> is the label for the expression when it is stored and
  printed.
  See the SpecPlot class for more information on the arguments to plotf and
  the corresponding output.

  There are three "special" names for printf: "sweep", "time", and "score".
  If "sweep" is given, for instance, printf will display the sweep count on each
  iteration. To display the value of an actual Venture variable named sweep,
  enclose it in a (labelled) statement. For instance:
  [INFER (printf sweep (labelled sweep var_sweep))].
  The three names above are just treated as normal Venture variables for
  peek and plotf.

  WARNING: Expressions are recorded the first time they are encountered in an
  inference program. For example, consider the program:
  [INFER (cycle ((peek x) (mh default one 1) (plotf l0 x)) 10)].
  In this program, the mh proposal could change the value of x. The value
  recorded for the iteration will be the value BEFORE the change, since x
  appears in a "peek" statement before. On the other hand, in the inference
  statement [INFER (cycle ((mh default one 1) (peek x) (plotf l0 x)) 10)],
  the value of x will be the value AFTER the proposal.
  If knowledge of x both before and after inference is desired, simply label
  x differently in the statements before and after inference:
  [INFER (cycle ((peek (labelled x x_before))
                 (mh default one 1)
                 (plotf l0 (labelled x x_after))) 10)]

  The dataset() method returns all data requested by any of the above commands
  as a Pandas DataFrame. By default, this data frame will always include the
  sweep count, particle id, wall time, and global log score.
  Calling print will generate all plots stored in the spec_plot attribute. This
  attribute in turn is a SpecPlot object.
  '''
  def __init__(self, first_command, filenames = None, callback=None):
    self.sweep = 0
    self.time = time.time()
    self._first_command = first_command
    self._peek_names = None
    self._peek_exprs = None
    self._peek_stack_dicts = None
    self._print_names = None
    self._print_exprs = None
    self._print_stack_dicts = None
    self._final_appended = False
    self.spec_plot = None
    self.filenames = filenames
    self.callback = callback

  def _init_peek(self, names, exprs, stack_dicts):
    self._peek_names = names
    self._peek_exprs = exprs
    self._peek_stack_dicts = stack_dicts

  def _init_print(self, names, exprs, stack_dicts):
    self._print_names = names
    self._print_exprs = exprs
    self._print_stack_dicts = stack_dicts

  def _init_plot(self, spec, names, exprs, stack_dicts):
    self.spec_plot = SpecPlot(spec, names, exprs, stack_dicts)

  def _add_data(self, engine, command):
    # if it's the first command, add all the default fields and increment the counter
    if command == self._first_command:
      self.sweep += 1
      self._save_previous_iter(self.sweep)
      self._collect_default_streams(engine)
    self._collect_requested_streams(engine, command)

  def _save_previous_iter(self, sweep):
    # self._this_iter_data always defined on sweep 1
    # pylint: disable=access-member-before-definition
    if sweep == 1:
      pass
    elif sweep == 2:
      self.data = self._this_iter_data
    else:
      for field in self.data:
        self.data[field].extend(self._this_iter_data[field])
    # reset the data to record the current iteration
    self._this_iter_data = {}

  def _collect_default_streams(self, engine):
    the_time = time.time() - self.time
    self._this_iter_data['sweep count'] = [self.sweep] * engine.num_traces()
    self._this_iter_data['particle id'] = range(engine.num_traces())
    self._this_iter_data['time (s)'] = [the_time] * engine.num_traces()
    self._this_iter_data['log score'] = engine.logscore_all()
    log_weights = copy(engine.trace_handler.log_weights)
    self._this_iter_data['particle log weight'] = log_weights
    self._this_iter_data['particle normalized prob'] = logWeightsToNormalizedDirect(log_weights)

  def _collect_requested_streams(self, engine, command):
    if command == 'peek':
      names = self._peek_names
      stack_dicts = self._peek_stack_dicts
    elif command == 'printf':
      names = self._print_names
      stack_dicts = self._print_stack_dicts
    else:
      names = self.spec_plot.names
      stack_dicts = self.spec_plot.stack_dicts
    for name, stack_dict in zip(names, stack_dicts):
      if name not in self._this_iter_data and stack_dict is not None:
        self._this_iter_data[name] = engine.sample_all(stack_dict)

  def _print_data(self):
    for name in self._print_names:
      if name == 'sweep':
        print 'Sweep count: {0}'.format(self.sweep)
      elif name == 'time':
        print 'Wall time: {0:0.2f} s'.format(self._this_iter_data['time (s)'][0])
      elif name == 'score':
        print 'Global log score: {0}'.format(self._this_iter_data['log score'])
      else:
        # TODO: support for pretty-printing of floats
        print '{0}: {1}'.format(name, strip_types_from_dict_values(self._this_iter_data)[name])
    print

  def dataset(self):
    ds = DataFrame.from_dict(strip_types_from_dict_values(self.data))
    cols = ds.columns
    first_cols = Index(['sweep count', 'particle id', 'time (s)', 'log score',
                        'particle log weight', 'particle normalized prob'])
    rest_cols = cols - first_cols
    order = first_cols.tolist() + rest_cols.tolist()
    return ds[order]

  def panel(self):
    '''
    Returns a Pandas Panel, a 3-d data structure. Use case is for multiple
    particles. In this case, each particle gets its own "slice". So, calling
    panel[0] returns the traces for all variables, for the first particle.
    '''
    ix = ['sweep count', 'particle id']
    return self.dataset().set_index(ix).to_panel().transpose(2,1,0)

  def draw(self):
    return self.spec_plot.draw(self.dataset())

  def plot(self):
    self.spec_plot.plot(self.dataset(), self.filenames)

  def __str__(self):
    "Not really a string method, but does get itself displayed when printed."
    if self.spec_plot is None and self.callback is None:
      return self.__repr__()
    elif self.spec_plot is not None and self.callback is None:
      self.plot()
      if self.filenames is None:
        return "a plot"
      else:
        return "plots saved to {}.".format(', '.join(self.filenames))
    else:
      self.callback(self.dataset())
      return ""

class SpecPlot(object):
  """(plotf spec exp0 ...) -- Generate a plot according to a format specification.

  Example:
    [INFER (cycle ((mh default one 1) (plotf c0s x)) 1000)]
  will do 1000 iterations of MH and then show a plot of the x variable
  (which should be a scalar) against the sweep number (from 1 to
  1000), colored according to the global log score.

  By passing a "labelled" statement to the format spec, Venture statements can
  be assigned labels (see InferResult documentation for more details):
    [INFER (cycle ((mh default one 1) (plotf c0s (labelled (normal 0 1) foo))) 1000)]
  will plot a draw from a normal distribution against the sweep number, and label
  the x axis as "foo".

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

  TODO: Modifiers for how to treat multiple particles: distinguished
  (current implementation, good default), mean, median, all (what
  exactly would all mean?  2-D table? Splice and hope?)

  TODO: Modifiers for how to treat overplotting?  (Exactly identical
  discrete samples; continuous samples that are close enough for the
  points to overlap; control or good choice of point size?; 2D kernel
  density nonsense?)

  If one stream is indicated for a 2-D plot (points or lines), the x
  axis is filled in with the sweep counter.  If three streams are
  indicated, the third is mapped to color.

  If the given specification is a list, make all those plots at once.

  """
  def __init__(self, spec, names, exprs, stack_dicts):
    self.spec_string = spec
    if spec is not None:
      self.spec = PlotSpec(spec)
    self.names = names
    self.exprs = exprs
    self.stack_dicts = stack_dicts

  def draw(self, data):
    if self.spec is None:
      pass
    else:
      return self.spec.draw(data, self.names)

  def plot(self, data, filenames=None):
    if self.spec is None:
      pass
    else:
      return self.spec.plot(data, self.names, filenames)
