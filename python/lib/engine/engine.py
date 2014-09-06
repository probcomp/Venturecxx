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
import pickle
import time
import queue
import sys
from functools import partial
import multiprocessing as mp
from multiprocessing import dummy as mpd
from abc import ABCMeta

from venture.exception import VentureException
from venture.lite.utils import sampleLogCategorical
from venture.engine.inference import Infer
from venture.engine.utils import expToDict
import venture.value.dicts as v

class Engine(object):

  def __init__(self, name="phony", Trace=None):
    self.name = name
    self.Trace = Trace
    self.weights = [1]
    self.directiveCounter = 0
    self.directives = {}
    self.inferrer = None
    self.trace_handler = SequentialTraceHandler([Trace()])
    import venture.lite.inference_sps as inf
    self.foreign_sps = {}
    self.inference_sps = dict(inf.inferenceSPsList)

  def inferenceSPsList(self):
    return self.inference_sps.iteritems()

  def bind_foreign_inference_sp(self, name, sp):
    self.inference_sps[name] = sp

  def getDistinguishedTrace(self):
    assert self.traces
    return self.traces[0]

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return self.directiveCounter

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()
    exp = datum

    value = self.trace_handler.delegate('assume', baseAddr, id, exp)

    self.directives[self.directiveCounter] = ["assume",id,datum]

    return (self.directiveCounter,value)

  def predict_all(self,datum):
    baseAddr = self.nextBaseAddr()

    value = self.trace_handler.delegate('predict_all', baseAddr, datum)

    self.directives[self.directiveCounter] = ["predict",datum]

    return (self.directiveCounter,value)

  def predict(self, datum):
    (did, answers) = self.predict_all(datum)
    return (did, answers[0])

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()

    self.trace_handler.delegate('observe', baseAddr, datum, val)

    self.directives[self.directiveCounter] = ["observe",datum,val]
    return self.directiveCounter

  def forget(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot forget a non-existent directive id",
                             argument="directive_id", directive_id=directiveId)
    directive = self.directives[directiveId]

    self.trace_handler.delegate('forget', directive, directiveId)

    del self.directives[directiveId]

  def sample(self,datum):
    # TODO Officially this is taken care of by the Venture SIVM level,
    # but I want it here because it is used in the interpretation of
    # the "peek" infer command.  Design clarification time?
    # TODO With this definition of "sample", "peek" will pump the
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

  def report_value(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot report a non-existent directive id",
                             argument=directiveId)
    return self.getDistinguishedTrace().extractValue(directiveId)

  def report_raw(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument",
                             "Cannot report raw value of a non-existent directive id",
                             argument=directiveId)
    return self.getDistinguishedTrace().extractRaw(directiveId)

  def clear(self):
    del self.trace_handler
    self.directiveCounter = 0
    self.directives = {}
    self.trace_handler = TraceHandler()
    self.ensure_rng_seeded_decently()

  def ensure_rng_seeded_decently(self):
    # Frobnicate the trace's random seed because Trace() resets the
    # RNG seed from the current time, which sucks if one calls this
    # method often.
    self.set_seed(random.randint(1,2**31-1))

  def bind_foreign_sp(self, name, sp):
    self.foreign_sps[name] = sp
    if self.name != "lite":
      # wrap it for backend translation
      import venture.lite.foreign as f
      sp = f.ForeignLiteSP(sp)

    self.trace_handler.delegate('bind_foreign_sp', name, sp)

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

  def resample(self, P):
    P = int(P)
    newTraces = [None for p in range(P)]
    for p in range(P):
      parent = sampleLogCategorical(self.trace_handler.weights) # will need to include or rewrite
      newTrace = self.copy_trace(self.traces[parent])
      newTraces[p] = newTrace
      if self.name != "lite":
        newTraces[p].set_seed(random.randint(1,2**31-1))
    self.traces = newTraces
    self.weights = [1 for p in range(P)]

  def infer(self, program):
    self.trace_handler.incorporate()
    if isinstance(program, list) and isinstance(program[0], dict) and program[0]["value"] == "loop":
      assert len(program) == 2
      prog = [v.sym("cycle"), program[1], v.number(1)]
      self.start_continuous_inference(prog)
    else:
      exp = self.macroexpand_inference(program)
      return self.infer_v1_pre_t(exp, Infer(self))

  def macroexpand_inference(self, program):
    if type(program) is list and type(program[0]) is dict and program[0]["value"] == "cycle":
      assert len(program) == 3
      subkernels = self.macroexpand_inference(program[1])
      transitions = self.macroexpand_inference(program[2])
      return [program[0], [v.sym("list")] + subkernels, transitions]
    elif type(program) is list and type(program[0]) is dict and program[0]["value"] == "mixture":
      assert len(program) == 3
      weights = []
      subkernels = []
      weighted_ks = self.macroexpand_inference(program[1])
      transitions = self.macroexpand_inference(program[2])
      for i in range(len(weighted_ks)/2):
        j = 2*i
        k = j + 1
        weights.append(weighted_ks[j])
        subkernels.append(weighted_ks[k])
      return [program[0], [v.sym("simplex")] + weights, [v.sym("array")] + subkernels, transitions]
    elif type(program) is list and type(program[0]) is dict and program[0]["value"] == 'peek':
      assert len(program) >= 2
      return [program[0]] + [v.quote(e) for e in program[1:]]
    elif type(program) is list and type(program[0]) is dict and program[0]["value"] == "printf":
      assert len(program) >= 2
      return [program[0]] + [v.quote(e) for e in program[1:]]
    elif type(program) is list and type(program[0]) is dict and program[0]["value"] == "plotf":
      assert len(program) >= 2
      return [program[0]] + [v.quote(e) for e in program[1:]]
    elif type(program) is list: return [self.macroexpand_inference(p) for p in program]
    else: return program

  def infer_v1_pre_t(self, program, target):
    import venture.lite.trace as lite
    next_trace = lite.Trace()
    # TODO Import the enclosing lexical environment into the new trace?
    import venture.lite.inference_sps as inf
    import venture.lite.value as val
    all_scopes = [s for s in target.engine.getDistinguishedTrace().scope_keys()]
    symbol_scopes = [s for s in all_scopes if isinstance(s, basestring) and not s.startswith("default")]
    for hack in inf.inferenceKeywords + symbol_scopes:
      next_trace.bindPrimitiveName(hack, val.VentureSymbol(hack))
    for name,sp in self.inferenceSPsList():
      next_trace.bindPrimitiveSP(name, sp)
    self.install_inference_prelude(next_trace)
    next_trace.eval(4, [program, v.blob(target)])
    ans = next_trace.extractValue(4)
    assert isinstance(ans, dict)
    assert ans["type"] is "blob"
    assert isinstance(ans["value"], Infer)
    return ans["value"].final_data()

  def install_inference_prelude(self, next_trace):
    for did, (name, exp) in enumerate(_inference_prelude()):
      next_trace.eval(did, exp)
      next_trace.bindInGlobalEnv(name, did)

  def primitive_infer(self, exp):
    self.trace_handler.delegate('primitive_infer', exp)

  def get_logscore(self, did): return self.trace_handler.delegate_distinguished('getDirectiveLogScore', did)
  def logscore(self): return self.trace_handler.delegate_distinguished('getDirectiveLogScore')
  def logscore_all(self): return self.trace_handler.delegate('getGlobalLogScore')

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.delegate_distinguished('numRandomChoices') }

  def get_seed(self):
    return self.delegate_distinguished('get_seed') # TODO is this what we want?

  def set_seed(self, seed):
    self.delegate_distinguished('set_seed', seed) # TODO is this what we want?

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

  def copy_trace(self, trace):
    values = dump_trace(self.directives, trace, skipStackDictConversion=True)
    return restore_trace(self.Trace(), self.directives,
                         values, skipStackDictConversion=True)

  def save(self, fname, extra=None):
    data = {}
    data['traces'] = [dump_trace(self.directives, trace) for trace in self.traces]
    data['weights'] = self.weights
    data['directives'] = self.directives
    data['directiveCounter'] = self.directiveCounter
    data['extra'] = extra
    version = '0.2'
    with open(fname, 'w') as fp:
      pickle.dump((data, version), fp)

  def load(self, fname):
    with open(fname) as fp:
      (data, version) = pickle.load(fp)
    assert version == '0.2', "Incompatible version or unrecognized object"
    self.directiveCounter = data['directiveCounter']
    self.directives = data['directives']
    self.traces = [restore_trace(self.Trace(), self.directives, trace) for trace in data['traces']]
    self.weights = data['weights']
    return data['extra']

  def convert(self, EngineClass):
    engine = EngineClass()
    engine.directiveCounter = self.directiveCounter
    engine.directives = self.directives
    engine.traces = []
    for trace in self.traces:
      values = dump_trace(self.directives, trace)
      engine.traces.append(restore_trace(self.Trace(), self.directives, values))
    engine.weights = self.weights
    return engine

  def to_lite(self):
    from venture.lite.engine import Engine as LiteEngine
    return self.convert(LiteEngine)

  def to_puma(self):
    from venture.puma.engine import Engine as PumaEngine
    return self.convert(PumaEngine)

  def profile_data(self):
    from pandas import DataFrame
    rows = []
    for (pid, trace) in enumerate([t for t in self.traces if hasattr(t, "stats")]):
      for (name, attempts) in trace.stats.iteritems():
        for (t, accepted) in attempts:
          rows.append({"name":str(name), "particle":pid, "time":t, "accepted":accepted})
    ans = DataFrame.from_records(rows)
    print ans
    return ans

# Methods for trace serialization

def dump_trace(directives, trace, skipStackDictConversion=False):
  db = trace.makeSerializationDB()

  for did, directive in sorted(directives.items(), reverse=True):
    if directive[0] == "observe":
      trace.unobserve(did)
    trace.unevalAndExtract(did, db)

  for did, directive in sorted(directives.items()):
    trace.restore(did, db)
    if directive[0] == "observe":
      trace.observe(did, directive[2])

  return trace.dumpSerializationDB(db, skipStackDictConversion)

def restore_trace(trace, directives, values, skipStackDictConversion=False):
  db = trace.makeSerializationDB(values, skipStackDictConversion)

  for did, directive in sorted(directives.items()):
      if directive[0] == "assume":
          name, datum = directive[1], directive[2]
          trace.evalAndRestore(did, datum, db)
          trace.bindInGlobalEnv(name, did)
      elif directive[0] == "observe":
          datum, val = directive[1], directive[2]
          trace.evalAndRestore(did, datum, db)
          trace.observe(did, val)
      elif directive[0] == "predict":
          datum = directive[1]
          trace.evalAndRestore(did, datum, db)

  return trace

  # TODO: Add methods to inspect/manipulate the trace for debugging and profiling

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
      # TODO React somehow to peeks and plotfs in the inference program
      # Currently suppressed for fear of clobbering the prompt
      self.engine.infer(program)
      time.sleep(0.0001) # Yield to be a good citizen

  def stop(self):
    inferrer = self.inferrer
    self.inferrer = None # Grab the semaphore
    inferrer.join()

def safely(f):
  # catches all exceptions that happen in the worker processes, so that they
  # can be passed back up to the handler and raised there
  def wrapped(*args, **kwargs):
    try:
      res = f(*args, **kwargs)
    except Exception as exception:
      return exception
    else:
      return res
  return wrapped

def check_process_results(res):
  n_exceptions = sum([isinstance(entry, Exception) for entry in res])
  if n_exceptions:
    errstr = ('{0} workers returned exceptions. The exception  messages are listed below\n'.
              format(n_exceptions))
    for i, entry in res:
      if isinstance(entry, Exception):
        errstr.append('{0} : {1}\n'.format(i, entry.message))
    raise VentureException(errstr)

# Classes to handle parallelization
class HandlerBase(object):
  '''Base class to delegate handling of parallel traces'''
  __metaclass__ = ABCMeta
  def __init__(self, traces):
    self.pipes = []
    self.processes = []
    self.weights = []
    Pipe, TraceProcess = self._setup()
    for trace in traces:
      parent, child = Pipe()
      process = TraceProcess(trace, child)
      self.pipes.append(parent)
      self.processes.append(process)
      self.weights.append(1)
    self._create_delegated_methods()

  def __del__(self):
    # stop child processes
    for process in self.processes: process.stop()

  def incorporate(self):
    weight_increments = self.delegate('makeConsistent')
    for weight, increment in zip(self.weights, weight_increments):
      weight += increment

  # NOTE: I could metaprogram all the methods that delegate passes on,
  # but it feels cleaner just call the delegator than to add another level
  # of wrapping
  def delegate(self, cmd, *args, **kwargs):
    # send command
    for pipe in self.pipes: pipe.send((cmd, args, kwargs))
    # wait for traces to finish
    for process in self.processes: process.join()
    # retrieve results
    res = []
    for pipe in self.pipes:
      res.append(pipe.recv())
    # check for exceptions
    check_process_results(res)
    return res

  def delegate_distinguished(self, cmd, *args, **kwargs):
    # issue a command only to the first worker process
    distinguished_pipe = self.pipes[0]
    distinguished_process = self.processes[0]
    distinguished_pipe.send((cmd, args, kwargs))
    distinguished_process.join()
    res = distinguished_pipe.recv()
    if isinstance(res, Exception):
      errstr = 'The distinguished worker returned the following exception: {0}'.format(res.message)
      raise VentureException(errstr)
    return res

  def retrieve_trace(self, trace, directives, i):
    # retrieve the trace attached to the ith process
    process = self.processes[i]
    dumped = process.send_trace(directives)
    restored = restore_trace(trace, directives, dumped)
    return restored

class ParallelTraceHandler(HandlerBase):
  def _setup(self):
    return mp.Pipe, ParallelTraceProcess

class SequentialTraceHandler(HandlerBase):
  def _setup(self):
    return mpd.Pipe, SequentialTraceProcess

class ProcessBase(object):
  '''
  Base class providing the methods used by both ParallelTraceProcess and
  SequentialTraceProcess. This uniformizes the inferface.
  '''
  __metaclass__ = ABCMeta
  def __init__(self, trace, pipe):
    self.trace = trace
    self.pipe = pipe
    Process = mp.Process if issubclass(self. mp.Process) else mpd.Process
    Process.__init__(self)

  @safely
  def __getattr__(self, attrname):
    # if attrname isn't attribute of ProcessBase, look for the attribute on the trace
    return getarr(self.trace, attrname)

  def stop(self):
    sys.exit()

  def run(self):
    while True:
      cmd, args, kwargs = self.pipe.recv()
      res = getatrr(self, cmd)(*args, **kwargs)
      pipe.send(res)

  def send_trace(self, directives):
    dumped = dump_trace(directives, self.trace)
    return dumped

  @safely
  def assume(self, baseAddr, id, exp):
    self.trace.eval(baesAddr, exp)
    self.trace.bindInGlobalEnv(id, baseAddr)
    return self.trace.extractValue(baseAddr)

  @safely
  def predict_all(self, baseAddr, datum):
    self.trace.eval(baseAddr,datum)
    return self.t.extractValue(baseAddr)

  @safely
  def observe(self, baseAddr, datum, val):
    trace.eval(baseAddr, datum)
    logDensity = trace.observe(baseAddr,val)
    # TODO check for -infinity? Throw an exception?
    if logDensity == float("-inf"):
      raise VentureException("invalid_constraint", "Observe failed to constrain",
                             expression=datum, value=val)

  @safely
  def forget(self, directive, directiveId):
    if directive[0] == "observe": trace.unobserve(directiveId)
    trace.uneval(directiveId)
    if directive[0] == "assume": trace.unbindInGlobalEnv(directive[1])

  @safely
  def freeze(self, directiveId):
    self.trace.freeze(directiveId)

  @safely
  def bind_foreign_sp(self, name, sp):
    self.trace.bindPrimitiveSP(name, sp)

  @safely
  def primitive_infer(self, exp):
    if hasattr(self.trace, "infer_exp"):
      # The trace can handle the inference primitive syntax natively
      self.trace.infer_exp(exp)
    else:
      # The trace cannot handle the inference primitive syntax
      # natively, so translate.
      self.trace.infer(expToDict(exp))

class ParallelTraceProcess(ProcessBase, mp.Process):
  '''Multiprocessing-based paralleism by inheritance'''
  pass

class SequentialTraceProcess(ProcessBase, mpd.Process):
  '''Sequential execution by inheritance'''
  pass



the_prelude = None

def _inference_prelude():
  global the_prelude
  if the_prelude is None:
    the_prelude = _compute_inference_prelude()
  return the_prelude

def _compute_inference_prelude():
  ans = []
  for (name, form) in [
        ["cycle", """(lambda (ks iter)
  (iterate (sequence ks) iter))"""],
        ["iterate", """(lambda (f iter)
  (if (<= iter 1)
      f
      (lambda (t) (f ((iterate f (- iter 1)) t)))))"""],
        ["sequence", """(lambda (ks)
  (if (is_pair ks)
      (lambda (t) ((sequence (rest ks)) ((first ks) t)))
      (lambda (t) t)))"""],
        ["mixture", """(lambda (weights kernels transitions)
  (iterate (lambda (t) ((categorical weights kernels) t)) transitions))"""]]:
    from venture.parser.church_prime_parser import ChurchPrimeParser
    from venture.sivm.macro import desugar_expression
    from venture.sivm.core_sivm import _modify_expression
    exp = _modify_expression(desugar_expression(ChurchPrimeParser.instance().parse_expression(form)))
    ans.append((name, exp))
  return ans
