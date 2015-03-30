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
import dill
import time

from venture.exception import VentureException
from trace_set import TraceSet
from venture.engine.inference import Infer
import venture.value.dicts as v

class Engine(object):

  def __init__(self, name="phony", Trace=None, persistent_inference_trace=False):
    self.name = name
    self.model = TraceSet(self, Trace)
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

  def define(self, id, datum):
    assert self.persistent_inference_trace, "Define only works if the inference trace is persistent"
    return self._define_in(id, datum, self.infer_trace)

  def _define_in(self, id, datum, trace):
    self.directiveCounter += 1
    did = self.directiveCounter # Might be changed by reentrant execution
    trace.eval(did, datum)
    trace.bindInGlobalEnv(id, did)
    return (did,trace.extractValue(did))

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()
    return (self.directiveCounter,self.model.define(baseAddr,id,datum))

  def predict_all(self,datum):
    baseAddr = self.nextBaseAddr()
    values = self.model.evaluate(baseAddr, datum)
    return (self.directiveCounter,values)

  def predict(self, datum):
    (did, answers) = self.predict_all(datum)
    return (did, answers[0])

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()
    self.model.observe(baseAddr, datum, val)
    return self.directiveCounter

  def forget(self,directiveId):
    self.model.forget(directiveId)

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
    self.model.freeze(directiveId)

  def report_value(self,directiveId):
    return self.model.report_value(directiveId)

  def report_raw(self,directiveId):
    return self.model.report_raw(directiveId)

  def bind_foreign_sp(self, name, sp):
    self.foreign_sps[name] = sp
    self.model.bind_foreign_sp(name, sp)

  def clear(self):
    self.model.clear()
    self.directiveCounter = 0

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

  def in_model(self, model, action):
    current_model = self.model
    self.model = model
    try:
      return self.infer_v1_pre_t(v.quote(action), Infer(self))
    finally:
      self.model = current_model

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

  def stop_continuous_inference(self):
    if self.inferrer is not None:
      # Running CI in Python
      self.inferrer.stop()
      self.inferrer = None

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
