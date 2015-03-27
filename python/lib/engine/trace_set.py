import cPickle as pickle

from ..multiprocess import (SynchronousMaster,
                            SynchronousSerializingMaster, ThreadedMaster,
                            ThreadedSerializingMaster, MultiprocessingMaster)
import trace as tr
from venture.lite.utils import sampleLogCategorical, logaddexp

class TraceSet(object):

  def __init__(self, engine, Trace=None):
    self.engine = engine # Because it contains the foreign sp registry and other misc stuff for restoring traces
    self.Trace = Trace
    self.mode = 'sequential'
    self.process_cap = None
    self.model = self.create_handler([tr.Trace(Trace())])

  def model_constructor(self, mode):
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

  def create_handler(self, traces, weights=None):
    if self.engine.name == "lite":
      local_rng = False
    else:
      local_rng = True
    ans = self.model_constructor(self.mode)(traces, self.process_cap, local_rng)
    if weights is not None:
      self.log_weights = weights
    else:
      self.log_weights = [0 for _ in traces]
    return ans

  def define(self, baseAddr, id, datum):
    values = self.model.map('define', baseAddr, id, datum)
    return values[0]

  def evaluate(self, baseAddr, datum):
    return self.model.map('evaluate', baseAddr, datum)

  def observe(self, baseAddr, datum, val):
    self.model.map('observe', baseAddr, datum, val)

  def forget(self, directiveId):
    self.model.map('forget', directiveId)

  def freeze(self, directiveId):
    self.model.map('freeze', directiveId)

  def report_value(self,directiveId):
    return self.model.at_distinguished('report_value', directiveId)

  def report_raw(self,directiveId):
    return self.model.at_distinguished('report_raw', directiveId)

  def bind_foreign_sp(self, name, sp):
    # check that we can pickle it
    if (not is_picklable(sp)) and (self.mode != 'sequential'):
      errstr = '''SP not picklable. To bind it, call [infer (resample_sequential <n_particles>)],
      bind the sp, then switch back to multiprocess.'''
      raise TypeError(errstr)

    self.model.map('bind_foreign_sp', name, sp)

  def clear(self):
    del self.model
    self.model = self.create_handler([tr.Trace(self.Trace())])

  def reinit_inference_problem(self, num_particles=1):
    """Unincorporate all observations and return to the prior.

First perform a resample with the specified number of particles
(default 1).  The choice of which particles will be returned to the
prior matters if the particles have different priors, as might happen
if freeze has been used.

    """
    self.resample(num_particles)
    # Resample currently reincorporates, so clear the weights again
    self.log_weights = [0 for _ in range(num_particles)]
    self.model.map('reset_to_prior')

  def resample(self, P, mode = 'sequential', process_cap = None):
    self.mode = mode
    self.process_cap = process_cap
    newTraces = self._resample_traces(P)
    del self.model
    self.model = self.create_handler(newTraces)
    self.incorporate()

  def _resample_traces(self, P):
    P = int(P)
    newTraces = [None for p in range(P)]
    used_parents = {}
    for p in range(P):
      parent = sampleLogCategorical(self.log_weights) # will need to include or rewrite
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
    del self.model
    self.model = self.create_handler(new_traces, new_weights)

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
    del self.model
    self.model = self.create_handler(new_ts, new_ws)

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
    self.log_weights = self.model.map('likelihood_weight')

  def incorporate(self):
    weight_increments = self.model.map('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.log_weights[i] += increment

  def primitive_infer(self, exp):
    self.model.map('primitive_infer', exp)

  def logscore(self): return self.model.at_distinguished('getGlobalLogScore')
  def logscore_all(self): return self.model.map('getGlobalLogScore')

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.model.at_distinguished('numRandomChoices') }

  def retrieve_dump(self, ix):
    return self.model.at(ix, 'dump')

  def retrieve_dumps(self):
    return self.model.map('dump')

  def retrieve_trace(self, ix):
    if self.model.can_shortcut_retrieval():
      return self.model.retrieve(ix)
    else:
      dumped = self.retrieve_dump(ix)
      return self.restore_trace(dumped)

  def retrieve_traces(self):
    if self.model.can_shortcut_retrieval():
      return self.model.retrieve_all()
    else:
      dumped_all = self.retrieve_dumps()
      return [self.restore_trace(dumped) for dumped in dumped_all]

  def dump_trace(self, trace, skipStackDictConversion=False):
    return trace.dump(skipStackDictConversion)
 
  def restore_trace(self, values, skipStackDictConversion=False):
    return tr.Trace.restore(self.engine, values, skipStackDictConversion)

  def copy_trace(self, trace):
    return self.engine.copy_trace(trace)

  def saveable(self):
    data = {}
    data['mode'] = self.mode
    data['traces'] = self.retrieve_dumps()
    data['log_weights'] = self.log_weights
    return data

  def load(self, data):
    traces = [self.restore_trace(trace) for trace in data['traces']]
    del self.model
    self.model = self.create_handler(traces, data['log_weights'])
    self.mode = data['mode']

  def convertFrom(self, other):
    traces = [self.restore_trace(dump) for dump in other.retrieve_dumps()]
    self.mode = other.mode
    self.model = self.create_handler(traces, other.log_weights)

  def set_profiling(self, enabled=True): 
      self.model.map('set_profiling', enabled)

  def clear_profiling(self):
    self.model.map('clear_profiling')

def is_picklable(obj):
  try:
    pickle.dumps(obj)
  except TypeError:
    return False
  except pickle.PicklingError:
    return False
  else:
    return True
