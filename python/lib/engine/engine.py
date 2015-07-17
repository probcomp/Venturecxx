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
import threading
import dill
import time
from contextlib import contextmanager

from venture.exception import VentureException
from trace_set import TraceSet
from venture.engine.inference import Infer
import venture.value.dicts as v
import venture.lite.value as vv

class Engine(object):

  def __init__(self, backend, persistent_inference_trace=True):
    self.model = TraceSet(self, backend)
    self.swapped_model = False
    self.directiveCounter = 0
    self.inferrer = None
    import venture.lite.inference_sps as inf
    self.foreign_sps = {}
    self.inference_sps = dict(inf.inferenceSPsList)
    self.callbacks = {}
    self.persistent_inference_trace = persistent_inference_trace
    if self.persistent_inference_trace:
      self.infer_trace = self.init_inference_trace()
    self.ripl = None
    self.creation_time = time.time()

  def num_traces(self):
    return len(self.model.log_weights)

  def inferenceSPsList(self):
    return self.inference_sps.iteritems()

  def bind_foreign_inference_sp(self, name, sp):
    self.inference_sps[name] = sp
    if self.persistent_inference_trace:
      self.infer_trace.bindPrimitiveSP(name, sp)

  def bind_callback(self, name, callback):
    self.callbacks[name] = callback

  def getDistinguishedTrace(self):
    return self.model.retrieve_trace(0)

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return self.directiveCounter

  def predictNextDirectiveId(self):
    # Careful: this prediction will be wrong if another thread does
    # something before the directive id is actually assigned.
    return self.directiveCounter + 1

  def define(self, id, datum):
    assert self.persistent_inference_trace, "Define only works if the inference trace is persistent"
    return self._define_in(id, datum, self.infer_trace)

  def _define_in(self, id, datum, trace):
    did = self.nextBaseAddr()
    trace.eval(did, datum)
    trace.bindInGlobalEnv(id, did)
    return (did, trace.extractValue(did))

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()
    return (baseAddr, self.model.define(baseAddr,id,datum))

  def predict_all(self,datum):
    baseAddr = self.nextBaseAddr()
    values = self.model.evaluate(baseAddr, datum)
    return (baseAddr, values)

  def predict(self, datum):
    (did, answers) = self.predict_all(datum)
    return (did, answers[0])

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()
    self.model.observe(baseAddr, datum, val)
    if True: # TODO: add flag to toggle auto-incorporation
      self.incorporate()
    return baseAddr

  def forget(self,directiveId):
    self.model.forget(directiveId)

  def force(self,datum,val):
    # TODO: The directive counter increments, but the "force" isn't added
    # to the list of directives
    # This mirrors the implementation in the core_sivm, but could be changed?
    did = self.observe(datum, val)
    self.incorporate()
    self.forget(did)
    return did

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
    self.model.freeze(directiveId)

  def report_value(self,directiveId):
    return self.model.report_value(directiveId)

  def report_raw(self,directiveId):
    return self.model.report_raw(directiveId)

  def register_foreign_sp(self, name, sp):
    self.foreign_sps[name] = sp

  def import_foreign(self, name):
    self.model.bind_foreign_sp(name, self.foreign_sps[name])

  def clear(self):
    self.model.clear()
    self.directiveCounter = 0
    if self.persistent_inference_trace:
      self.infer_trace = self.init_inference_trace()
    # TODO The clear operation appears to be bit-rotten.  Problems include:
    # - Doesn't clean up the sivm's and ripl's per-directive records
    # - Not clear what it should do with foreign SPs (remove the
    #   dictionaries or rebind them in the new traces?)
    # - Not clear what it should do with the parallelism mode and
    #   other such auxiliary state.

  # TODO There should also be capture_inference_problem and
  # restore_inference_problem (Analytics seems to use something like
  # it)
  def reinit_inference_problem(self, num_particles=1):
    self.model.reinit_inference_problem(num_particles)

  def resample(self, P, mode = 'sequential', process_cap = None):
    self.model.resample(P, mode, process_cap)

  def diversify(self, program): self.model.diversify(program)
  def collapse(self, scope, block): self.model.collapse(scope, block)
  def collapse_map(self, scope, block): self.model.collapse_map(scope, block)
  def likelihood_weight(self): self.model.likelihood_weight()
  def incorporate(self): self.model.incorporate()

  def evaluate(self, program):
    with self.inference_trace():
      did = self._do_evaluate(program)
      ans = self.infer_trace.extractValue(did)
      self.infer_trace.uneval(did) # TODO This becomes "forget" after the engine.Trace wrapper
      # Return the forgotten did to better coordinate with the sivm
      return (did, ans)

  def _do_evaluate(self, program):
    did = self.nextBaseAddr()
    self.infer_trace.eval(did, program)
    return did

  def in_model(self, model, action):
    current_model = self.model
    current_swapped_status = self.swapped_model
    self.model = model
    # TODO asStackDict doesn't do the right thing because it tries to
    # be politely printable.  Maybe I should change that.
    stack_dict_action = {"type":"SP", "value":action}
    program = [v.sym("run"), v.quote(stack_dict_action)]
    try:
      self.swapped_model = True
      with self.inference_trace():
        did = self._do_evaluate(program)
        ans = self.infer_trace.extractRaw(did)
        self.infer_trace.uneval(did) # TODO This becomes "forget" after the engine.Trace wrapper
        return (ans, model)
    finally:
      self.model = current_model
      self.swapped_model = current_swapped_status

  def infer(self, program):
    if self.is_infer_loop_program(program):
      assert len(program) == 2
      self.start_continuous_inference(program[1])
      return (None, None) # The core_sivm expects a 2-tuple
    else:
      return self.evaluate([v.sym("run"), program])

  def is_infer_loop_program(self, program):
    return isinstance(program, list) and isinstance(program[0], dict) and program[0]["value"] == "loop"

  @contextmanager
  def inference_trace(self):
    if not self.persistent_inference_trace:
      self.infer_trace = self.init_inference_trace()
    try:
      yield
    finally:
      if not self.persistent_inference_trace:
        self.infer_trace = None

  def init_inference_trace(self):
    import venture.untraced.trace as trace
    ans = trace.Trace()
    for name,sp in self.inferenceSPsList():
      ans.bindPrimitiveSP(name, sp)
    import venture.lite.inference_sps as inf
    for word in inf.inferenceKeywords:
      if not ans.boundInGlobalEnv(word):
        ans.bindPrimitiveName(word, vv.VentureSymbol(word))
    ans.bindPrimitiveName("__the_inferrer__", vv.VentureForeignBlob(Infer(self)))
    self.install_inference_prelude(ans)
    return ans

  def install_inference_prelude(self, next_trace):
    for name, exp in _inference_prelude():
      self._define_in(name, exp, next_trace)

  def primitive_infer(self, exp): self.model.primitive_infer(exp)
  def logscore(self): return self.model.logscore()
  def logscore_all(self): return self.model.logscore_all()
  def get_entropy_info(self): return self.model.get_entropy_info()

  def get_seed(self):
    return self.model.traces.at_distinguished('get_seed') # TODO is this what we want?

  def set_seed(self, seed):
    self.model.traces.at_distinguished('set_seed', seed) # TODO is this what we want?

  def continuous_inference_status(self):
    if self.inferrer is not None:
      # Running CI in Python
      return {"running":True, "expression":self.inferrer.program}
    else:
      return {"running":False}

  def start_continuous_inference(self, program):
    self.stop_continuous_inference()
    self.inferrer = ContinuousInferrer(self, program)
    self.inferrer.start()

  def stop_continuous_inference(self):
    if self.inferrer is not None:
      # Running CI in Python
      self.inferrer.stop()
      self.inferrer = None

  def on_continuous_inference_thread(self):
    inferrer_obj = self.inferrer # Read self.inferrer atomically, just in case.
    # The time that self.inferrer is not None is a superset of
    # lifetime of the continuous inference thread.
    if inferrer_obj is None:
      return False
    # Otherwise, the first thing the continuous inference thread does
    # is set the inference_thread_id to its identifier, so if it is
    # unset (or not equal to the current thread identifier), this
    # thread is not the CI thread.
    else:
      return inferrer_obj.inference_thread_id == threading.currentThread().ident


  def save(self, fname, extra=None):
    data = self.model.saveable()
    data['directiveCounter'] = self.directiveCounter
    data['extra'] = extra
    version = '0.2'
    with open(fname, 'w') as fp:
      dill.dump((data, version), fp)

  def load(self, fname):
    with open(fname) as fp:
      (data, version) = dill.load(fp)
    assert version == '0.2', "Incompatible version or unrecognized object"
    self.directiveCounter = data['directiveCounter']
    self.model.load(data)
    return data['extra']

  def convert(self, backend):
    engine = backend.make_engine(self.persistent_inference_trace)
    if self.persistent_inference_trace:
      engine.infer_trace = self.infer_trace # TODO Copy?
    engine.directiveCounter = self.directiveCounter
    engine.model.convertFrom(self.model)
    return engine

  def to_lite(self):
    from venture.shortcuts import Lite
    return self.convert(Lite())

  def to_puma(self):
    from venture.shortcuts import Puma
    return self.convert(Puma())

  def set_profiling(self, enabled=True): self.model.set_profiling(enabled)
  def clear_profiling(self): self.model.clear_profiling()

  def profile_data(self):
    rows = []
    for (pid, trace) in enumerate([t for t in self.model.retrieve_traces()
                                   if hasattr(t, "stats")]):
      for stat in trace.stats:
        rows.append(dict(stat, particle = pid))

    return rows

# Support for continuous inference

class ContinuousInferrer(object):
  def __init__(self, engine, program):
    self.engine = engine
    self.program = program
    self.inferrer = threading.Thread(target=self.infer_continuously, args=(self.program,))
    self.inferrer.daemon = True
    self.inference_thread_id = None

  def start(self):
    self.inferrer.start()

  def infer_continuously(self, program):
    self.inference_thread_id = threading.currentThread().ident
    # Can use the storage of the thread object itself as the semaphore
    # controlling whether continuous inference proceeds.
    while self.inferrer is not None:
      # TODO React somehow to values returned by the inference action?
      # Currently suppressed for fear of clobbering the prompt
      self.engine.ripl.infer(program)
      time.sleep(0.0001) # Yield to be a good citizen

  def stop(self):
    inferrer = self.inferrer
    self.inferrer = None # Grab the semaphore
    inferrer.join()

# Inference prelude

the_prelude = None

def _inference_prelude():
  global the_prelude # Yes, I do mean to use a global variable. pylint:disable=global-statement
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
