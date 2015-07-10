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

import time
from pandas import DataFrame
from copy import copy

from venture.lite.value import (VentureArray, VentureSymbol,
                                VentureInteger, VentureValue, VentureNil, VentureForeignBlob)
from venture.lite.types import (ExpressionType, SymbolType)
from venture.lite.utils import logWeightsToNormalizedDirect
from venture.ripl.utils import strip_types_from_dict_values
from venture.lite.exception import VentureValueError, VentureCallbackError
from trace_set import TraceSet
from plot_spec import PlotSpec

class Infer(object):
  def __init__(self, engine):
    self.engine = engine

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
    special_names = [VentureSymbol(x) for x in ['iteration', 'time', 'score']]
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
  def likelihood_weight(self): self.engine.likelihood_weight()
  def likelihood_at(self, scope, block):
    return self.engine.model.traces.map('likelihood_at', scope, block)
  def posterior_at(self, scope, block):
    return self.engine.model.traces.map('posterior_at', scope, block)
  def enumerative_diversify(self, scope, block): self.engine.diversify(["enumerative", scope, block])
  def collapse_equal(self, scope, block): self.engine.collapse(scope, block)
  def collapse_equal_map(self, scope, block): self.engine.collapse_map(scope, block)
  def incorporate(self): self.engine.incorporate()
  def printf(self, dataset): print dataset.asPandas()
  def plotf(self, spec, dataset):
    spec = ExpressionType().asPython(spec)
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names)
  def plotf_to_file(self, basenames, spec, dataset):
    filenames = ExpressionType().asPython(basenames)
    spec = ExpressionType().asPython(spec)
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names, self._format_filenames(filenames, spec))
  def sweep(self, dataset):
    print 'Iteration count: ' + str(dataset.asPandas()['iteration count'].values[-1])
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
    answer = {} # Map from column name to list of values; the values
                # are parallel to the particles
    std_names = ['iteration count', 'particle id', 'time (s)', 'log score',
                 'particle log weight', 'particle normalized prob']
    def collect_std_streams(engine):
      the_time = time.time() - engine.creation_time
      answer['iteration count'] = [1] * engine.num_traces()
      answer['particle id'] = range(engine.num_traces())
      answer['time (s)'] = [the_time] * engine.num_traces()
      answer['log score'] = engine.logscore_all() # TODO Replace this by explicit references to (global_likelihood), because the current implementation is wrong
      log_weights = copy(engine.model.log_weights)
      answer['particle log weight'] = log_weights
      answer['particle normalized prob'] = logWeightsToNormalizedDirect(log_weights)
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
    return [VentureValue.fromStackDict(val) for val in self.engine.sample_all(exp.asStackDict())]
  def extract_stats(self, exp):
    sp_dict = self.engine.sample(exp.asStackDict())
    return VentureValue.fromStackDict(sp_dict["aux"])
  def load_plugin(self, name, *args):
    return self.convert_none(self.engine.ripl.load_plugin(name, *args))

  def particle_log_weights(self):
    return self.engine.model.log_weights
  def set_particle_log_weights(self, new_weights):
    assert len(new_weights) == len(self.engine.model.log_weights)
    self.engine.model.log_weights = new_weights
  def particle_normalized_probs(self):
    return logWeightsToNormalizedDirect(self.particle_log_weights())

  def new_model(self, backend_name=None):
    if backend_name is None:
      return TraceSet(self.engine, self.engine.model.backend)
    else:
      import venture.shortcuts as s
      return TraceSet(self.engine, s.backend(backend_name))
  def in_model(self, model, action):
    return self.engine.in_model(model, action)
  def model_import_foreign(self, name):
    return self.engine.import_foreign(name)

  def select(self, scope, block):
    assert len(self.engine.model.log_weights) == 1, "Custom subproblems only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'select', scope, block)
  def detach(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_detach', scaffold)
  def regen(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_regen', scaffold)
  def restore(self, scaffold, rhoDB):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'just_restore', scaffold, rhoDB)
  def detach_for_proposal(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'detach_for_proposal', scaffold)
  def regen_with_proposal(self, scaffold, values):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'regen_with_proposal', scaffold, values)
  def get_current_values(self, scaffold):
    assert len(self.engine.model.log_weights) == 1, "Custom proposals only supported for one trace at a time"
    return self.engine.model.traces.at(0, 'get_current_values', scaffold)

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
    answer = {}
    for (key, vals) in self.data.iteritems():
      if key == "iteration count" and len(vals) > 0:
        nxt = max(vals)
        answer[key] = vals + [v + nxt for v in other.data[key]]
      else:
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
      if key == "iteration count" and len(self.data[key]) > 0:
        nxt = max(self.data[key])
        self.data[key].extend([v + nxt for v in other.data[key]])
      else:
        self.data[key].extend(other.data[key])
    return self

  def _check_compat(self, other):
    if not self.ind_names == other.ind_names:
      raise Exception("Cannot merge datasets with different contents %s %s" % (self.ind_names, other.ind_names))
    if not self.std_names == other.std_names:
      raise Exception("Cannot merge datasets with different contents %s %s" % (self.std_names, other.std_names))

  def asPandas(self):
    """Return a freshly allocated Pandas DataFrame containing the data in this Dataset."""
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
