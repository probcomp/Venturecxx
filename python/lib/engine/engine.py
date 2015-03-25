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
import random
import dill
import cPickle as pickle
import time

from venture.exception import VentureException
from ..multiprocess import (SynchronousMaster,
                            SynchronousSerializingMaster, ThreadedMaster,
                            ThreadedSerializingMaster, MultiprocessingMaster)
import trace as tr
from venture.lite.utils import sampleLogCategorical, logaddexp
from venture.engine.inference import Infer
import venture.value.dicts as v

def is_picklable(obj):
  try:
    res = pickle.dumps(obj)
  except TypeError:
    return False
  except pickle.PicklingError:
    return False
  else:
    return True

class Engine(object):

  def __init__(self, name="phony", Trace=None, persistent_inference_trace=False):
    self.name = name
    self.Trace = Trace
    self.directiveCounter = 0
    self.directives = {}
    self.inferrer = None
    self.mode = 'sequential'
    self.process_cap = None
    self.trace_handler = self.create_handler([tr.Trace(Trace())])
    import venture.lite.inference_sps as inf
    self.foreign_sps = {}
    self.inference_sps = dict(inf.inferenceSPsList)
    self.callbacks = {}
    self.persistent_inference_trace = persistent_inference_trace
    if self.persistent_inference_trace:
      self.infer_trace = self.init_inference_trace()
    self.ripl = None
    self.creation_time = time.time()

  def trace_handler_constructor(self, mode):
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
    if self.name == "lite":
      local_rng = False
    else:
      local_rng = True
    ans = self.trace_handler_constructor(self.mode)(traces, self.process_cap, local_rng)
    if weights is not None:
      self.log_weights = weights
    else:
      self.log_weights = [0 for _ in traces]
    return ans

  def num_traces(self):
    return len(self.log_weights)

  def inferenceSPsList(self):
    return self.inference_sps.iteritems()

  def bind_foreign_inference_sp(self, name, sp):
    self.inference_sps[name] = sp
    if self.persistent_inference_trace:
      self.infer_trace.bindPrimitiveSP(name, sp)

  def bind_callback(self, name, callback):
    self.callbacks[name] = callback

  def getDistinguishedTrace(self):
    return self.retrieve_trace(0)

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return self.directiveCounter

  def define(self, id, datum):
    assert self.persistent_inference_trace, "Define only works if the inference trace is persistent"
    return self._define_in(id, datum, self.infer_trace)

  def _define_in(self, id, datum, trace):
    self.directiveCounter += 1
    did = self.directiveCounter # Might be changed by reentrant execution
    trace.eval(did, datum)
    trace.bindInGlobalEnv(id, did)
    return (did,trace.extractValue(did))

  def _check_consistency_of_directive_map(self):
    model_dirs = self.retrieve_trace(0).directives
    for (k, v) in model_dirs.iteritems():
      assert k in self.directives
      assert self.directives[k][1:] == v[1:]
    for (k, v) in self.directives.iteritems():
      if v[0] in ["assume", "predict", "observe"]:
        assert k in model_dirs
        assert model_dirs[k][1:] == v[1:]

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()
    exp = datum

    values = self.trace_handler.delegate('define', baseAddr, id, exp)
    value = values[0]

    self.directives[self.directiveCounter] = ["assume",id,datum]
    self._check_consistency_of_directive_map()
    return (self.directiveCounter,value)

  def predict_all(self,datum):
    baseAddr = self.nextBaseAddr()

    value = self.trace_handler.delegate('evaluate', baseAddr, datum)

    self.directives[self.directiveCounter] = ["predict",datum]
    self._check_consistency_of_directive_map()

    return (self.directiveCounter,value)

  def predict(self, datum):
    (did, answers) = self.predict_all(datum)
    return (did, answers[0])

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()

    self.trace_handler.delegate('observe', baseAddr, datum, val)

    self.directives[self.directiveCounter] = ["observe",datum,val]
    self._check_consistency_of_directive_map()
    return self.directiveCounter

  def forget(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot forget a non-existent directive id",
                             argument="directive_id", directive_id=directiveId)
    directive = self.directives[directiveId]

    self.trace_handler.delegate('forget', directive, directiveId)

    del self.directives[directiveId]
    self._check_consistency_of_directive_map()

  def force(self,datum,val):
    # TODO: The directive counter increments, but the "force" isn't added
    # to the list of directives
    # This mirrors the implementation in the core_sivm, but could be changed?
    did = self.observe(datum, val)
    self.incorporate()
    self.forget(did)
    return self.directiveCounter

  def sample(self,datum):
    # TODO Officially this is taken care of by the Venture SIVM level,
    # but I want it here because it is used in the interpretation of
    # the "collect" infer command.  Design clarification time?
    # TODO With this definition of "sample", "collect" will pump the
    # directive counter of the engine.  That is likely to make us at
    # least somewhat sad.
    (did, value) = self.predict(datum)
    self.forget(did)
    return value

  def sample_all(self, datum):
    (did, values) = self.predict_all(datum)
    self.forget(did)
    return values

  def freeze(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot freeze a non-existent directive id",
                             argument="directive_id", directive_id=directiveId)
    # TODO Record frozen state for reinit_inference_problem?  What if
    # the replay is done with a different number of particles than the
    # original?  Where do the extra values come from?
    self.trace_handler.delegate('freeze', directiveId)
    # XXX OOPS!  We need to remember, in self.directives, that this
    # node is frozen at its current values, so that when we copy the
    # trace we don't make random choices afresh here.  But there's no
    # obvious way to record that.
    #self.directives[directiveId] = ["assume", directiveId, XXX]

  def report_value(self,directiveId):
    return self.trace_handler.delegate_distinguished('report_value', directiveId)

  def report_raw(self,directiveId):
    return self.trace_handler.delegate_distinguished('report_raw', directiveId)

  def bind_foreign_sp(self, name, sp):
    self.foreign_sps[name] = sp
    if self.name != "lite":
      # wrap it for backend translation
      import venture.lite.foreign as f
      sp = f.ForeignLiteSP(sp)

    # check that we can pickle it
    if (not is_picklable(sp)) and (self.mode != 'sequential'):
      errstr = '''SP not picklable. To bind it, call [infer (resample_sequential <n_particles>)],
      bind the sp, then switch back to multiprocess.'''
      raise TypeError(errstr)

    self.trace_handler.delegate('bind_foreign_sp', name, sp)

  def clear(self):
    del self.trace_handler
    self.directiveCounter = 0
    self.directives = {}
    self.trace_handler = self.create_handler([tr.Trace(self.Trace())])
    self.ensure_rng_seeded_decently()

  def ensure_rng_seeded_decently(self):
    # Frobnicate the trace's random seed because Trace() resets the
    # RNG seed from the current time, which sucks if one calls this
    # method often.
    self.set_seed(random.randint(1,2**31-1))

  # TODO There should also be capture_inference_problem and
  # restore_inference_problem (Analytics seems to use something like
  # it)
  def reinit_inference_problem(self, num_particles=None):
    """Blow away all the traces and rebuild from the stored directives.

The goal is to resample from the prior.  May have the unfortunate
effect of renumbering the directives, if some had been forgotten."""
    worklist = sorted(self.directives.iteritems())
    self.clear()
    if num_particles is not None:
      self.infer("(resample %d)" % num_particles)
    for (name,sp) in self.foreign_sps.iteritems():
      self.bind_foreign_sp(name,sp)
    for (_,dir) in worklist:
      self.replay(dir)

  def replay(self,directive):
    if directive[0] == "assume":
      self.assume(directive[1], directive[2])
    elif directive[0] == "observe":
      self.observe(directive[1], directive[2])
    elif directive[0] == "predict":
      self.predict(directive[1])
    else:
      assert False, "Unkown directive type found %r" % directive

  def resample(self, P, mode = 'sequential', process_cap = None):
    self.mode = mode
    self.process_cap = process_cap
    newTraces = self._resample_traces(P)
    del self.trace_handler
    self.trace_handler = self.create_handler(newTraces)
    self.incorporate()

  def _resample_traces(self, P):
    P = int(P)
    newTraces = [None for p in range(P)]
    for p in range(P):
      parent = sampleLogCategorical(self.log_weights) # will need to include or rewrite
      newTrace = self.copy_trace(self.retrieve_trace(parent))
      newTraces[p] = newTrace
    return newTraces

  def diversify(self, program):
    traces = self.retrieve_traces()
    weights = self.log_weights
    new_traces = []
    new_weights = []
    for (t, w) in zip(traces, weights):
      for (res_t, res_w) in zip(*(t.diversify(program, self.copy_trace))):
        new_traces.append(res_t)
        new_weights.append(w + res_w)
    del self.trace_handler
    self.trace_handler = self.create_handler(new_traces, new_weights)

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
    del self.trace_handler
    self.trace_handler = self.create_handler(new_ts, new_ws)

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
    self.log_weights = self.trace_handler.delegate('likelihood_weight')

  def incorporate(self):
    weight_increments = self.trace_handler.delegate('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.log_weights[i] += increment

  def infer(self, program):
    self.incorporate()
    if self.is_infer_loop_program(program):
      assert len(program) == 2
      prog = [v.sym("do")] + program[1]
      self.start_continuous_inference(prog)
    else:
      return self.infer_v1_pre_t(program, Infer(self))

  def is_infer_loop_program(self, program):
    return isinstance(program, list) and isinstance(program[0], dict) and program[0]["value"] == "loop"

  def infer_v1_pre_t(self, program, target):
    if not self.persistent_inference_trace:
      self.infer_trace = self.init_inference_trace()
    self.install_self_evaluating_scope_hack(self.infer_trace, target)
    try:
      self.directiveCounter += 1
      did = self.directiveCounter # Might be mutated by reentrant execution
      self.infer_trace.eval(did, [program, v.blob(target)])
      ans = self.infer_trace.extractValue(did)
      # Expect the result to be a Venture pair of the "value" of the
      # inference action together with the mutated Infer object.
      assert isinstance(ans, dict)
      assert ans["type"] is "improper_list"
      (vs, tail) = ans["value"]
      assert tail["type"] is "blob"
      assert isinstance(tail["value"], Infer)
      assert len(vs) == 1
      return vs[0]
    except VentureException:
      if self.persistent_inference_trace:
        self.remove_self_evaluating_scope_hack(self.infer_trace, target)
      else:
        self.infer_trace = None
      raise
    else:
      if self.persistent_inference_trace:
        self.remove_self_evaluating_scope_hack(self.infer_trace, target)
      else:
        self.infer_trace = None
      raise

  def init_inference_trace(self):
    import venture.lite.trace as lite
    ans = lite.Trace()
    for name,sp in self.inferenceSPsList():
      ans.bindPrimitiveSP(name, sp)
    self.install_inference_prelude(ans)
    return ans

  def symbol_scopes(self, target):
    all_scopes = [s for s in target.engine.getDistinguishedTrace().scope_keys()]
    symbol_scopes = [s for s in all_scopes if isinstance(s, basestring) and not s.startswith("default")]
    return symbol_scopes

  def install_self_evaluating_scope_hack(self, next_trace, target):
    import venture.lite.inference_sps as inf
    import venture.lite.value as val
    symbol_scopes = self.symbol_scopes(target)
    for hack in inf.inferenceKeywords + symbol_scopes:
      if not next_trace.globalEnv.symbolBound(hack):
        next_trace.bindPrimitiveName(hack, val.VentureSymbol(hack))

  def remove_self_evaluating_scope_hack(self, next_trace, target):
    import venture.lite.inference_sps as inf
    symbol_scopes = self.symbol_scopes(target)
    for hack in inf.inferenceKeywords + symbol_scopes:
      if next_trace.globalEnv.symbolBound(hack):
        next_trace.unbindInGlobalEnv(hack)

  def install_inference_prelude(self, next_trace):
    for name, exp in _inference_prelude():
      self._define_in(name, exp, next_trace)

  def primitive_infer(self, exp):
    self.trace_handler.delegate('primitive_infer', exp)

  def logscore(self): return self.trace_handler.delegate_distinguished('getGlobalLogScore')
  def logscore_all(self): return self.trace_handler.delegate('getGlobalLogScore')

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.trace_handler.delegate_distinguished('numRandomChoices') }

  def get_seed(self):
    return self.trace_handler.delegate_distinguished('get_seed') # TODO is this what we want?

  def set_seed(self, seed):
    self.trace_handler.delegate_distinguished('set_seed', seed) # TODO is this what we want?

  def continuous_inference_status(self):
    if self.inferrer is not None:
      # Running CI in Python
      return {"running":True, "expression":self.inferrer.program}
    else:
      return {"running":False}

  def start_continuous_inference(self, program):
    self.stop_continuous_inference()
    self.inferrer = ContinuousInferrer(self, program)

  def stop_continuous_inference(self):
    if self.inferrer is not None:
      # Running CI in Python
      self.inferrer.stop()
      self.inferrer = None

  def retrieve_dump(self, ix):
    return self.trace_handler.delegate_one(ix, 'dump', self.directives)

  def retrieve_dumps(self):
    return self.trace_handler.delegate('dump', self.directives)

  def retrieve_trace(self, ix):
    if self.trace_handler.can_shortcut_retrieval():
      return self.trace_handler.retrieve(ix)
    else:
      dumped = self.retrieve_dump(ix)
      return self.restore_trace(dumped)

  def retrieve_traces(self):
    if self.trace_handler.can_shortcut_retrieval():
      return self.trace_handler.retrieve_all()
    else:
      dumped_all = self.retrieve_dumps()
      return [self.restore_trace(dumped) for dumped in dumped_all]

  # class methods that call the corresponding functions, with arguments filled in
  def dump_trace(self, trace, skipStackDictConversion=False):
    return trace.dump(self.directives, skipStackDictConversion)

  def restore_trace(self, values, skipStackDictConversion=False):
    return tr.Trace.restore(self, values, skipStackDictConversion)

  def copy_trace(self, trace):
    values = self.dump_trace(trace, skipStackDictConversion=True)
    return self.restore_trace(values, skipStackDictConversion=True)

  def save(self, fname, extra=None):
    data = {}
    data['traces'] = self.retrieve_dumps()
    data['log_weights'] = self.log_weights
    data['directives'] = self.directives
    data['directiveCounter'] = self.directiveCounter
    data['mode'] = self.mode
    data['extra'] = extra
    version = '0.2'
    with open(fname, 'w') as fp:
      dill.dump((data, version), fp)

  def load(self, fname):
    with open(fname) as fp:
      (data, version) = dill.load(fp)
    assert version == '0.2', "Incompatible version or unrecognized object"
    self.directiveCounter = data['directiveCounter']
    self.directives = data['directives']
    self.mode = data['mode']
    traces = [self.restore_trace(trace) for trace in data['traces']]
    del self.trace_handler
    self.trace_handler = self.create_handler(traces, data['log_weights'])
    return data['extra']

  def convert(self, EngineClass):
    engine = EngineClass()
    engine.directiveCounter = self.directiveCounter
    engine.directives = self.directives
    engine.mode = self.mode
    traces = [engine.restore_trace(dump) for dump in self.retrieve_dumps()]
    engine.trace_handler = engine.create_handler(traces, self.log_weights)
    return engine

  def to_lite(self):
    from venture.lite.engine import Engine as LiteEngine
    return self.convert(LiteEngine)

  def to_puma(self):
    from venture.puma.engine import Engine as PumaEngine
    return self.convert(PumaEngine)

  def set_profiling(self, enabled=True):
    # TODO: do this by introspection on the trace
    if self.name == 'lite':
      self.trace_handler.delegate('set_profiling', enabled)

  def clear_profiling(self):
    self.trace_handler.delegate('clear_profiling', enabled)

  def profile_data(self):
    rows = []
    for (pid, trace) in enumerate([t for t in self.retrieve_traces()
                                   if hasattr(t, "stats")]):
      for stat in trace.stats:
        rows.append(dict(stat, particle = pid))

    return rows

class ContinuousInferrer(object):
  def __init__(self, engine, program):
    self.engine = engine
    self.program = program
    import threading as t
    self.inferrer = t.Thread(target=self.infer_continuously, args=(self.program,))
    self.inferrer.daemon = True
    self.inferrer.start()

  def infer_continuously(self, program):
    # Can use the storage of the thread object itself as the semaphore
    # controlling whether continuous inference proceeds.
    while self.inferrer is not None:
      # TODO React somehow to values returned by the inference action?
      # Currently suppressed for fear of clobbering the prompt
      self.engine.ripl.infer(program, suppress_pausing_continous_inference=True)
      time.sleep(0.0001) # Yield to be a good citizen

  def stop(self):
    inferrer = self.inferrer
    self.inferrer = None # Grab the semaphore
    inferrer.join()

# inference prelude

the_prelude = None

def _inference_prelude():
  global the_prelude
  if the_prelude is None:
    the_prelude = _compute_inference_prelude()
  return the_prelude

def _compute_inference_prelude():
  ans = []
  import inference_prelude
  for (name, _desc, form) in inference_prelude.prelude:
    from venture.parser.church_prime.parse import ChurchPrimeParser
    from venture.sivm.macro_system import desugar_expression
    from venture.sivm.core_sivm import _modify_expression
    exp = _modify_expression(desugar_expression(ChurchPrimeParser.instance().parse_expression(form)))
    ans.append((name, exp))
  return ans
