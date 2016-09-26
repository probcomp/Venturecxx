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

import cPickle as pickle
import contextlib
import copy
import random

import numpy.random as npr

from ..multiprocess import MultiprocessingMaster
from ..multiprocess import SynchronousMaster
from ..multiprocess import SynchronousSerializingMaster
from ..multiprocess import ThreadedMaster
from ..multiprocess import ThreadedSerializingMaster
from venture.exception import VentureException
from venture.lite.utils import log_domain_even_out
from venture.lite.utils import logaddexp
from venture.lite.utils import sampleLogCategorical
import venture.engine.trace as tr

class TraceSet(object):

  def __init__(self, engine, backend, seed):
    self.engine = engine # Because it contains the foreign sp registry and other misc stuff for restoring traces
    self.backend = backend
    self.mode = 'sequential'
    self.process_cap = None
    self.traces = None
    assert seed is not None
    self._py_rng = random.Random(seed)
    seed = self._py_rng.randint(1, 2**31 - 1)
    trace = tr.Trace(self.backend.trace_constructor()(seed))
    self.create_trace_pool([trace])
    self._did_to_label = {}
    self._label_to_did = {}

  def _trace_master(self, mode):
    if mode == 'multiprocess':
      return MultiprocessingMaster
    elif mode == 'thread_ser':
      return ThreadedSerializingMaster
    elif mode == 'threaded':
      return ThreadedMaster
    elif mode == 'serializing':
      return SynchronousSerializingMaster
    else:
      return SynchronousMaster

  def create_trace_pool(self, traces, weights=None):
    del self.traces # To (try and) force reaping any worker processes
    seed = self._py_rng.randint(1, 2**31 - 1)
    self.traces = self._trace_master(self.mode)(traces, self.process_cap, seed)
    if weights is not None:
      self.log_weights = weights
    else:
      self.log_weights = [0 for _ in traces]

  # Labeled operations.

  @contextlib.contextmanager
  def _putting_label(self, label, did):
    if label in self._label_to_did:
      raise VentureException('invalid_argument',
          'Label %r is already assigned to a different directive.' % (label,),
          argument='label')
    assert did not in self._did_to_label, \
        'did %r already has label %r, not %r' % \
        (did, self._did_to_label[did], label)
    yield
    assert label not in self._label_to_did, \
      'Label %r mysteriously appeared in model!' % (label,)
    assert did not in self._did_to_label
    self._label_to_did[label] = did
    self._did_to_label[did] = label

  def _get_label(self, label):
    if label not in self._label_to_did:
      raise VentureException('invalid_argument',
          'Label %r does not exist.' % (label,),
          argument='label')
    return self._label_to_did[label]

  @contextlib.contextmanager
  def _forgetting_label(self, label):
    if label not in self._label_to_did:
      raise VentureException('invalid_argument',
          'Label %r does not exist.' % (label,),
          argument='label')
    did = self._label_to_did[label]
    assert label == self._did_to_label[did]
    yield self._label_to_did[label]
    assert did == self._label_to_did[label]
    assert did not in self._did_to_label
    del self._label_to_did[label]

  def get_directive_id(self, label):
    return self._get_label(label)

  def get_directive_label(self, did):
    return self._did_to_label.get(did)

  def labeled_define(self, label, baseAddr, id, exp):
    with self._putting_label(label, baseAddr):
      return self.define(baseAddr, id, exp)

  def labeled_observe(self, label, baseAddr, exp, val):
    with self._putting_label(label, baseAddr):
      self.observe(baseAddr, exp, val)

  def labeled_evaluate(self, label, baseAddr, exp):
    with self._putting_label(label, baseAddr):
      return self.evaluate(baseAddr, exp)

  def labeled_forget(self, label):
    with self._forgetting_label(label) as directiveId:
      return self.forget(directiveId)

  def labeled_freeze(self, label):
    directiveId = self._get_label(label)
    self.freeze(directiveId)

  def labeled_report_value(self, label):
    directiveId = self._get_label(label)
    return self.report_value(directiveId)

  def labeled_report_raw(self, label):
    directiveId = self._get_label(label)
    return self.report_raw(directiveId)

  # Unlabeled operations.

  def define(self, baseAddr, id, datum):
    values = self.traces.map('define', baseAddr, id, datum)
    return values[0]

  def evaluate(self, baseAddr, datum):
    return self.traces.map('evaluate', baseAddr, datum)

  def observe(self, baseAddr, datum, val):
    self.traces.map('observe', baseAddr, datum, val)

  def forget(self, directiveId):
    weights = self.traces.map('forget', directiveId)
    if directiveId in self._did_to_label:
      del self._did_to_label[directiveId]
    return weights

  def freeze(self, directiveId):
    self.traces.map('freeze', directiveId)

  def report_value(self,directiveId):
    return self.traces.at_distinguished('report_value', directiveId)

  def report_raw(self,directiveId):
    return self.traces.at_distinguished('report_raw', directiveId)

  def bind_foreign_sp(self, name, sp):
    # check that we can pickle it
    if (self.mode != 'sequential') and (not is_picklable(sp)):
      errstr = '''SP not picklable. To bind it, call [infer (resample_sequential <n_particles>)],
      bind the sp, then switch back to multiprocess.'''
      raise TypeError(errstr)

    self.traces.map('bind_foreign_sp', name, sp)

  def clear(self):
    seed = self._py_rng.randint(1, 2**31 - 1)
    trace = tr.Trace(self.backend.trace_constructor()(seed))
    self.create_trace_pool([trace])
    self._label_to_did = {}
    self._did_to_label = {}

  def reinit_inference_problem(self, num_particles=1):
    """Return to the prior.

First perform a resample with the specified number of particles
(default 1).  The choice of which particles will be returned to the
prior matters if the particles have different priors, as might happen
if freeze has been used.

    """
    self.resample(num_particles)
    # Resample currently reincorporates, so clear the weights again
    self.log_weights = [0 for _ in range(num_particles)]
    self.traces.map('reset_to_prior')

  def resample(self, P, mode = 'sequential', process_cap = None):
    self.mode = mode
    self.process_cap = process_cap
    newTraces = self._resample_traces(P)
    self.create_trace_pool(newTraces, log_domain_even_out(self.log_weights, P))
    self.incorporate()

  def _resample_traces(self, P):
    P = int(P)
    newTraces = [None for p in range(P)]
    used_parents = {}
    seed = self._py_rng.randint(1, 2**31 - 1)
    np_rng = npr.RandomState(seed)
    for p in range(P):
      parent = sampleLogCategorical(self.log_weights, np_rng) # will need to include or rewrite
      newTrace = self._use_parent(used_parents, parent)
      newTraces[p] = newTrace
    return newTraces

  def _use_parent(self, used_parents, index):
    # All traces returned from calling this function with the same
    # used_parents dict need to be unique (since they should be
    # allowed to diverge in the future).
    #
    # Subject to that, minimize copying and retrieval (copying is
    # currently always expensive, and retrieval can be if it involves
    # serialization).  Invariant: never need to retrieve a trace more
    # than once.
    if index in used_parents:
      return self.copy_trace(used_parents[index])
    else:
      parent = self.retrieve_trace(index)
      used_parents[index] = parent
      return parent

  def diversify(self, program):
    traces = self.retrieve_traces()
    weights = self.log_weights
    new_traces = []
    new_weights = []
    for (t, w) in zip(traces, weights):
      for (res_t, res_w) in zip(*(t.diversify(program, self.copy_trace))):
        new_traces.append(res_t)
        new_weights.append(w + res_w)
    self.create_trace_pool(new_traces, new_weights)

  def _collapse_help(self, scope, block, select_keeper):
    traces = self.retrieve_traces()
    weights = self.log_weights
    fingerprints = [t.block_values(scope, block) for t in traces]
    def grouping():
      "Because sorting doesn't do what I want on dicts, so itertools.groupby is not useful"
      groups = [] # :: [(fingerprint, [trace], [weight])]  Not a dict because the fingerprints are not hashable
      for (t, w, f) in zip(traces, weights, fingerprints):
        try:
          place = [g[0] for g in groups].index(f)
        except ValueError:
          place = len(groups)
          groups.append((f, [], []))
        groups[place][1].append(t)
        groups[place][2].append(w)
      return groups
    groups = grouping()
    new_ts = []
    new_ws = []
    for (_, ts, ws) in groups:
      (index, total) = select_keeper(ws)
      new_ts.append(self.copy_trace(ts[index]))
      new_ts[-1].makeConsistent() # Even impossible states ok
      new_ws.append(total)
    self.create_trace_pool(new_ts, new_ws)

  def collapse(self, scope, block):
    def sample(weights):
      return (sampleLogCategorical(weights), logaddexp(weights))
    self._collapse_help(scope, block, sample)

  def collapse_map(self, scope, block):
    # The proper behavior in the Viterbi algorithm is to weight the
    # max particle by its own weight, not by the total weight of its
    # whole bucket.
    def max_ind(lst):
      return (lst.index(max(lst)), max(lst))
    self._collapse_help(scope, block, max_ind)

  def likelihood_weight(self):
    self.log_weights = self.traces.map('likelihood_weight')

  def incorporate(self):
    weight_increments = self.traces.map('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.log_weights[i] += increment
    return weight_increments

  def for_each_trace_sequential(self, f):
    # Rather than sending the engine to the traces, bring the traces
    # to the engine.
    # TODO is there any way to do something like this while leveraging
    # parallelism?
    mode = self.mode
    self.mode = 'sequential'
    traces = self.retrieve_traces()
    weights = self.log_weights
    try:
      res = []
      new_traces = []
      new_weights = []
      for trace, weight in zip(traces, weights):
        self.create_trace_pool([trace], [weight])
        ans = f(trace)
        res.append(ans)
        new_traces += self.retrieve_traces()
        new_weights += self.log_weights
      traces = new_traces
      weights = new_weights
      return res
    finally:
      self.mode = mode
      self.create_trace_pool(traces, weights)

  def on_trace(self, i, f):
    mode = self.mode
    self.mode = 'sequential'
    traces = self.retrieve_traces()
    weights = self.log_weights
    try:
      self.create_trace_pool([traces[i]], [weights[i]])
      ans = f(traces[i])
      new_traces = self.retrieve_traces()
      new_weights = self.log_weights
      traces = traces[0:i] + new_traces + traces[i+1:]
      weights = weights[0:i] + new_weights + weights[i+1:]
      return ans
    finally:
      self.mode = mode
      self.create_trace_pool(traces, weights)

  def primitive_infer(self, exp):
    return self.traces.map('primitive_infer', exp)

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.traces.at_distinguished('numRandomChoices') }

  def retrieve_dump(self, ix):
    return self.traces.at(ix, 'dump')

  def retrieve_dumps(self):
    return self.traces.map('dump')

  def retrieve_trace(self, ix):
    if self.traces.can_shortcut_retrieval():
      return self.traces.retrieve(ix)
    else:
      dumped = self.retrieve_dump(ix)
      return self.restore_trace(dumped)

  def retrieve_traces(self):
    if self.traces.can_shortcut_retrieval():
      return self.traces.retrieve_all()
    else:
      dumped_all = self.retrieve_dumps()
      return [self.restore_trace(dumped) for dumped in dumped_all]

  def restore_trace(self, values, skipStackDictConversion=False):
    mktrace_seed = self.backend.trace_constructor()
    mktrace = lambda: mktrace_seed(self._py_rng.randint(1, 2**31 - 1))
    return tr.Trace.restore(mktrace, values, self.engine.foreign_sps, skipStackDictConversion)

  def copy_trace(self, trace):
    if trace.short_circuit_copyable():
      return trace.stop_and_copy()
    else:
      values = trace.dump(skipStackDictConversion=True)
      return self.restore_trace(values, skipStackDictConversion=True)

  def saveable(self):
    data = {}
    data['mode'] = self.mode
    data['traces'] = self.retrieve_dumps()
    data['log_weights'] = self.log_weights
    data['label_dict'] = self._label_to_did
    data['did_dict'] = self._did_to_label
    return data

  def load(self, data):
    traces = [self.restore_trace(trace) for trace in data['traces']]
    self.mode = data['mode']
    self.create_trace_pool(traces, data['log_weights'])
    self._label_to_did = data['label_dict']
    self._did_to_label = data['did_dict']

  def convertFrom(self, other):
    traces = [self.restore_trace(dump) for dump in other.retrieve_dumps()]
    self.mode = other.mode
    self.create_trace_pool(traces, other.log_weights)
    self._did_to_label = copy.copy(other._did_to_label)
    self._label_to_did = copy.copy(other._label_to_did)

  def set_profiling(self, enabled=True):
      self.traces.map('set_profiling', enabled)

  def clear_profiling(self):
    self.traces.map('clear_profiling')

def is_picklable(obj):
  try:
    pickle.dumps(obj)
  except TypeError:
    return False
  except pickle.PicklingError:
    return False
  else:
    return True
