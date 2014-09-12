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

import multiprocessing as mp
from multiprocessing import dummy as mpd
from abc import ABCMeta, abstractmethod

from venture.exception import (TraceProcessException, VentureException,
                               exception_type_eq, exception_all_eq)
from venture.engine.utils import expToDict

# Methods for trace serialization

def dump_trace(trace, directives, skipStackDictConversion=False):
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

def safely(f):
  # pylint: disable=broad-except
  # in this use case, we want to catch all exceptions to avoid hanging
  def wrapped(*args, **kwargs):
    try:
      res = f(*args, **kwargs)
    except Exception as exception:
      return exception
    else:
      return res
  return wrapped

# The trace handlers; allow communication between the engine and the traces

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
      process.start()
      self.pipes.append(parent)
      self.processes.append(process)
      self.weights.append(1)

  def __del__(self):
    # stop child processes
    self.delegate('stop')

  def incorporate(self):
    weight_increments = self.delegate('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.weights[i] += increment

  # NOTE: I could metaprogram all the methods that delegate passes on,
  # but it feels cleaner just call the delegator than to add another level
  # of wrapping
  def delegate(self, cmd, *args, **kwargs):
    '''Delegate command to all workers'''
    # send command
    for pipe in self.pipes: pipe.send((cmd, args, kwargs))
    if cmd == 'stop': return
    res = []
    for pipe in self.pipes:
      res.append(pipe.recv())
    self._check_process_results(res)
    if cmd == 'assume':
      return res[0]
    else:
      return res

  def _check_process_results(self, res):
    exceptions = [entry for entry in res if isinstance(entry, Exception)]
    if exceptions:
      # if all exceptions are same, raise the first one
      if exception_all_eq(exceptions):
        raise exceptions[0]
      # if all exceptions are same type, raise exception of that type
      elif exception_type_eq(exceptions):
        raise self._format_exceptions(exceptions)
      # otherwise, raise a generic error message
      else:
        raise TraceProcessException(exceptions)

  @staticmethod
  def _format_exceptions(exceptions):
    exception_type = type(exceptions[0])
    message = 'The following exception messages were returned by the workers:\n'
    message += '\n'.join(sorted(set([exception.message for exception in exceptions])))
    return exception_type(message)

  def delegate_one(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single worker, indexed by ix'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs))
    res = pipe.recv()
    if isinstance(res, Exception): raise res
    return res

  def delegate_distinguished(self, cmd, *args, **kwargs):
    return self.delegate_one(0, cmd, *args, **kwargs)

  def retrieve_dump(self, ix, engine):
    return self.delegate_one(ix, 'send_dump', engine.directives)

  def retrieve_dumps(self, engine):
    return self.delegate('send_dump', engine.directives)

  @abstractmethod
  def retrieve_trace(self, ix, engine): pass

  @abstractmethod
  def retrieve_traces(self, engine): pass

class ParallelHandlerArchitecture(HandlerBase):
  def retrieve_trace(self, ix, engine):
    dumped = self.retrieve_dump(ix, engine)
    return engine.restore_trace(dumped)

  def retrieve_traces(self, engine):
    dumped_all = self.retrieve_dumps(engine)
    return [engine.restore_trace(dumped) for dumped in dumped_all]

class SequentialHandlerArchitecture(HandlerBase):
  def retrieve_trace(self, ix, engine):
    return self.delegate_one(ix, 'send_trace')

  def retrieve_traces(self, engine):
    return self.delegate('send_trace')

# These are the classes we actually use

class ParallelTraceHandler(ParallelHandlerArchitecture):
  @staticmethod
  def _setup():
    return mp.Pipe, ParallelTraceProcess

class EmulatingTraceHandler(ParallelHandlerArchitecture):
  @staticmethod
  def _setup():
    return mpd.Pipe, EmulatingTraceProcess

class SequentialTraceHandler(SequentialHandlerArchitecture):
  @staticmethod
  def _setup():
    return mpd.Pipe, SequentialTraceProcess


# The individual trace processes; hold the individual traces and communicate
# with the handlers via pipes

class ProcessBase(object):
  '''
  Base class providing the methods used by both ParallelTraceProcess and
  SequentialTraceProcess. This uniformizes the inferface.
  '''
  __metaclass__ = ABCMeta
  def __init__(self, trace, pipe):
    self.trace = trace
    self.pipe = pipe
    Process = self._setup()
    Process.__init__(self)
    self.daemon = True

  def run(self):
    while True:
      cmd, args, kwargs = self.pipe.recv()
      if cmd == 'stop':
        return
      res = getattr(self, cmd)(*args, **kwargs)
      self.pipe.send(res)

  def __getattr__(self, attrname):
    # if attrname isn't attribute of ProcessBase, look for it as a method on the trace
    # safely doesn't work as a decorator here; do it this way.
    return safely(getattr(self.trace, attrname))

  @safely
  def send_dump(self, directives):
    dumped = dump_trace(self.trace, directives)
    return dumped

  @safely
  def assume(self, baseAddr, id, exp):
    self.trace.eval(baseAddr, exp)
    self.trace.bindInGlobalEnv(id, baseAddr)
    return self.trace.extractValue(baseAddr)

  @safely
  def predict_all(self, baseAddr, datum):
    self.trace.eval(baseAddr,datum)
    return self.trace.extractValue(baseAddr)

  @safely
  def observe(self, baseAddr, datum, val):
    self.trace.eval(baseAddr, datum)
    logDensity = self.trace.observe(baseAddr,val)
    # TODO check for -infinity? Throw an exception?
    if logDensity == float("-inf"):
      raise VentureException("invalid_constraint", "Observe failed to constrain",
                             expression=datum, value=val)

  @safely
  def forget(self, directive, directiveId):
    if directive[0] == "observe": self.trace.unobserve(directiveId)
    self.trace.uneval(directiveId)
    if directive[0] == "assume": self.trace.unbindInGlobalEnv(directive[1])

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

class ParallelProcessArchitecture(ProcessBase):
  # Nothing new; just declared for explicitness
  pass

class SequentialProcessArchitecture(ProcessBase):
  @safely
  def send_trace(self):
    return self.trace

class MultiprocessBase(mp.Process):
  @staticmethod
  def _setup():
    return mp.Process

class DummyBase(mpd.Process):
  @staticmethod
  def _setup():
    return mpd.Process

# The actual classes we used are defined via inheritance
# pylint: disable=too-many-ancestors
# this is the cleanest way to do it
class ParallelTraceProcess(ParallelProcessArchitecture, MultiprocessBase):
  '''Multiprocessing-based paralleism by inheritance'''
  pass

class EmulatingTraceProcess(ParallelProcessArchitecture, DummyBase):
  '''Emulates multiprocessing by serializing traces before sending'''
  pass

class SequentialTraceProcess(SequentialProcessArchitecture, DummyBase):
  '''Does not serialize traces before sending'''
  pass
