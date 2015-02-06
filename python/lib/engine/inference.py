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
from pandas import DataFrame
from copy import copy

from venture.lite.value import (ExpressionType, SymbolType, VentureArray, VentureSymbol,
                                VentureInteger, VentureValue, VentureNil)
from venture.lite.utils import logWeightsToNormalizedDirect
from venture.ripl.utils import strip_types_from_dict_values
from venture.lite.exception import VentureValueError
from plot_spec import PlotSpec

class Infer(object):
  def __init__(self, engine):
    self.engine = engine
    self.out = {}
    self.result = None

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
  def printf(self, dataset): print dataset.asPandas()
  def plotf_to_file(self, basenames, spec, dataset):
    filenames = ExpressionType().asPython(basenames)
    spec = ExpressionType().asPython(spec)
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names, self._format_filenames(filenames, spec))
  def call_back(self, name, *exprs):
    name = SymbolType().asPython(name)
    if name not in self.engine.callbacks:
      raise VentureValueError("Unregistered callback {}".format(name))
    return self.convert_none(self.engine.callbacks[name](self, *[self.engine.sample_all(e.asStackDict()) for e in exprs]))
  def collect(self, *exprs):
    names, stack_dicts = self.parse_exprs(exprs, None)
    answer = {} # Map from column name to list of values; the values
                # are parallel to the particles
    std_names = ['sweep count', 'particle id', 'time (s)', 'log score',
                 'particle log weight', 'particle normalized prob']
    def collect_std_streams(engine):
      the_time = time.time() - engine.creation_time
      answer['sweep count'] = [1] * engine.num_traces()
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
  def plotf(self, spec, dataset):
    spec = ExpressionType().asPython(spec)
    # TODO I hope ind_names is right for the names of the spec plot
    PlotSpec(spec).plot(dataset.asPandas(), dataset.ind_names)

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
      if key == "sweep count" and len(vals) > 0:
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
      if key == "sweep count" and len(self.data[key]) > 0:
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
    ds = DataFrame.from_dict(strip_types_from_dict_values(self.data))
    order = self.std_names + self.ind_names
    return ds[order]
