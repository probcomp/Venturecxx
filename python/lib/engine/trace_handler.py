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

'''
This module handles the interface between the Venture engine (which is part of
the Venture stack), and the Venture traces (which are implemented in the
Venture backends). The architecture is as follows:

The TraceProcess classes are subclasses of either multiprocessing.Process, or
multiprocessing.dummy.Process.
Each instance of TraceProcess contains a single Trace as an attribute, and
interacts with the Trace via method calls. As a subclass of Process, each
instance has a run() method. The run() method is simply a listener; the
TraceProcess waits for commands sent over the pipe from the TraceHandler
(described below), calls the method associated with the command, and then
returns the result to the  Handler over the pipe. All methods are wrapped in
the @safely decorator, whose purpose is to cath all errors ocurring in workers
and return them over the Pipe, to be raised by the Handler. This prevents
exceptions in the child processes from hanging the program.
The TraceProcess classes are daemonic; the TraceHandler need not wait for
the run() methods of its children to complete before regaining control of
the program. Also as daemonic processes, all TraceProcess instances will
be terminated when the controlling Handler is deleted.
For more information on the TraceProcess class hierarchy, see the docstrings
below.

The TraceHandler classes facilitate communication between the Engine and the
individual TraceProcess instances. Each TraceHandler stores a list of
TraceProcesses, and also a list of Pipes interacting with those
TraceProcesses, as attributes.
When the Engine calls a method (say, engine.assume()), the TraceHandler passes
this command over the Pipes to the TraceProcesses via its "delegate" method,
and then waits for results to be returned from the workers. It regains control
of the program when all results have been returned. It then checks for
exceptions; if any are found, it re-raises the first one. Else it passes its
result back to the Engine.
The TraceHandler also has methods to retrieve serialized traces from the
individual TraceProcesses and reconstruct them. For the ParallelTraceHandler,
Traces must be serialized before being sent from TraceProcesses back to the
Handler. This is the case since Trace objects are not picklable and hence
cannot be sent over Pipes directly.
For more information on the TraceHandler class hierarchy, see the docstrings
below.
'''

import multiprocessing as mp
from multiprocessing import dummy as mpd
from abc import ABCMeta, abstractmethod
from sys import exc_info
from traceback import format_exc
import random
import numpy as np

from venture.exception import VentureException, format_worker_trace
from venture.engine.utils import expToDict

######################################################################
# Auxiliary functions for trace serialization and safe function evaluation
######################################################################

def dump_trace(trace, directives, skipStackDictConversion=False):
  # TODO: It would be good to pass foreign_sps to this function as well,
  # and then check that the passed foreign_sps match up with the foreign
  # SP's bound in the trace's global environment. However, in the Puma backend
  # there is currently no way to access this global environment.
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

def restore_trace(trace, directives, values, foreign_sps, skipStackDictConversion=False):
  for name, sp in foreign_sps.items():
    trace.bindPrimitiveSP(name, sp)

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
    except Exception:
      # If I return the traceback object and try to format it
      # higher up, it's just None. So, format it here.
      exc_type, value, traceback = exc_info()
      trace = format_exc(traceback)
      # If it's a VentureException, need to convert to JSON to send over pipe
      if isinstance(value, VentureException):
        value = value.to_json_object()
      return exc_type, value, trace
    else:
      return res
  return wrapped

def threw_error(entry):
  return (isinstance(entry, tuple) and
          (len(entry) == 3) and
          issubclass(entry[0], Exception))

######################################################################
# The trace handlers; allow communication between the engine and the traces
######################################################################

class HandlerBase(object):
  '''
  Base class for all TraceHandlers; defines the majority of the methods to
  interact with the TraceHandlers and reserves abstract methods with different
  behavior in parallel and sequential modes to be defined by subclasses.
  '''
  __metaclass__ = ABCMeta
  def __init__(self, traces, backend):
    self.backend = backend
    self.pipes = []
    self.processes = []
    self.weights = []
    Pipe, TraceProcess = self._setup()
    for trace in traces:
      parent, child = Pipe()
      process = TraceProcess(trace, child, self.backend)
      process.start()
      self.pipes.append(parent)
      self.processes.append(process)
      self.weights.append(1)
    self.reset_seeds()

  def __del__(self):
    # stop child processes
    self.delegate('stop')

  def incorporate(self):
    weight_increments = self.delegate('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.weights[i] += increment

  def reset_seeds(self):
    for i in range(len(self.processes)):
      self.delegate_one(i, 'set_seed', random.randint(1,2**31-1))

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
    if any([threw_error(entry) for entry in res]):
      exception_handler = TraceProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single worker, indexed by ix'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs))
    res = pipe.recv()
    if threw_error(res):
      exception_handler = TraceProcessExceptionHandler([res])
      raise exception_handler.gen_exception()
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

######################################################################

class ParallelHandlerArchitecture(HandlerBase):
  '''
  Retrieves traces by requesting dumps from workers and reconstructing on
  other end of Pipe. Inherited by ParallelTraceHandler (for which this mode
  of communication is required) and EmulatingTraceHandler (which is sequential
  but mimics the API of the Parallel version).
  '''
  def retrieve_trace(self, ix, engine):
    dumped = self.retrieve_dump(ix, engine)
    return engine.restore_trace(dumped)

  def retrieve_traces(self, engine):
    dumped_all = self.retrieve_dumps(engine)
    return [engine.restore_trace(dumped) for dumped in dumped_all]

class SequentialHandlerArchitecture(HandlerBase):
  '''
  Retrieves traces by requesting the traces themselves directly. Since
  multiprocessing.dummy is actually just a wrapper around Threading, there is
  no problem with sending arbitrary Python objects over dummy.Pipes. Inherited
  by SequentialTraceHandler.
  '''
  def retrieve_trace(self, ix, engine):
    return self.delegate_one(ix, 'send_trace')

  def retrieve_traces(self, engine):
    return self.delegate('send_trace')

######################################################################

class ParallelTraceHandler(ParallelHandlerArchitecture):
  '''
  Controls ParallelTraceProcesses. Communicates with workers via
  multiprocessing.Pipe. Truly parallel implementation.
  '''
  @staticmethod
  def _setup():
    return mp.Pipe, ParallelTraceProcess

class EmulatingTraceHandler(ParallelHandlerArchitecture):
  '''
  Controls EmulatingTraceProcesses. Communicates with workers via
  multiprocessing.dummy.Pipe. Do not use for actual modeling. Rather,
  intended for debugging; API mimics ParallelTraceHandler, but implementation
  is sequential.
  '''
  @staticmethod
  def _setup():
    return mpd.Pipe, EmulatingTraceProcess

class SequentialTraceHandler(SequentialHandlerArchitecture):
  '''
  Controls SequentialTraceProcess. Default TraceHandler. Communicates via
  multiprocessing.dummy.Pipe.
  '''
  @staticmethod
  def _setup():
    return mpd.Pipe, SequentialTraceProcess

######################################################################
# Trace processes; interact with individual traces
######################################################################

class ProcessBase(object):
  '''
  The base class is ProcessBase, which defines all the methods that do the
  actual work of interacting with traces.
  '''
  __metaclass__ = ABCMeta
  def __init__(self, trace, pipe, backend):
    self.trace = trace
    self.pipe = pipe
    self.backend = backend
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
    return safely(safely(getattr)(self.trace, attrname))

  @abstractmethod
  def send_trace(self): pass

  @safely
  def set_seed(self, seed):
    # if we're in puma or we're truly parallel, set the seed; else don't.
    if self.backend == 'puma':
      self.trace.set_seed(seed)

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

######################################################################

class ParallelProcessArchitecture(ProcessBase):
  '''
  Attempting to send a trace without first serializing results in an exception.
  Inherited by ParallelTraceProcess (for which this behavior is necessary) and
  EmulatingTraceProcess (which mimics the API of the Parallel process).
  '''
  @safely
  def send_trace(self):
    raise VentureException("fatal",
                           "Must serialize traces before sending in parallel architecture")

class SequentialProcessArchitecture(ProcessBase):
  '''
  Sends traces directly. Inherited by SequentialTraceProcess.
  '''
  @safely
  def send_trace(self):
    return self.trace

class MultiprocessBase(mp.Process):
  '''
  Specifies parallel implementation; inherited by ParallelTraceProcess.
  '''
  @staticmethod
  def _setup():
    return mp.Process

class DummyBase(mpd.Process):
  '''
  Specifies sequential implementation; inherited by EmulatingTraceProcess
  and SequentialTraceProcess.
  '''
  @staticmethod
  def _setup():
    return mpd.Process

######################################################################

# pylint: disable=too-many-ancestors
class ParallelTraceProcess(ParallelProcessArchitecture, MultiprocessBase):
  '''
  True parallel traces via multiprocessing. Controlled by ParallelTraceHandler.
  '''
  @safely
  def set_seed(self, seed):
    # override the default set_seed method; if we're in parallel Python,
    # reset the global random seeds.
    if self.backend == 'lite':
      random.seed(seed)
      np.random.seed(seed)
    else:
      ProcessBase.set_seed(self, seed)

class EmulatingTraceProcess(ParallelProcessArchitecture, DummyBase):
  '''
  Emulates ParallelTraceProcess but is implemented sequentially. Use for
  debugging. Controlled by EmulatingTraceHandler.
  '''
  pass

class SequentialTraceProcess(SequentialProcessArchitecture, DummyBase):
  '''
  Default class for interacting with Traces. Controlled by
  SequentialTraceHandler.
  '''
  pass

######################################################################
# Code to handle exceptions in worker processes
######################################################################

class TraceProcessExceptionHandler(object):
  '''
  Stores information on exceptions from the workers. By default, just finds
  the first exception, prints its original stack trace, and then re-raises.
  However, more information is kept around for inspection by the user during
  debugging.
  '''
  def __init__(self, res):
    self.info = [self._format_results(entry) for entry in res if threw_error(entry)]
    self.exc_types, self.values, self.traces = zip(*self.info)
    self.n_processes = len(res)
    self.n_errors = len(self.info)

  def gen_exception(self):
    # This is a hack of sorts; see long comment below.
    Exc = self.exc_types[0]
    if issubclass(Exc, VentureException):
      exc = self.values[0]
      exc.worker_trace = self.traces[0]
      return exc
    else:
      msg = (self.values[0].message + format_worker_trace(self.traces[0]))
      return Exc(msg)

  @staticmethod
  def _format_results(entry):
    if issubclass(entry[0], VentureException):
      value = VentureException.from_json_object(entry[1])
    else:
      value = entry[1]
    return (entry[0], value, entry[2])

# Concerning the hack above: In designing engines that handle parallel traces,
# we'd like errors in the child trace process to be passed back up to the engine.
# We'd then like the error from the child to be re-raised, displaying both the
# stack trace from the child and the parent.
# There is no easy way to do this in Python, so I made two hacks.
#   If the child exception is of type VentureException, store the child stack
#   trace as a string on the instance. Have the __str__ method print the child
#   stack trace along with the parent.
# If the child exception is of some other type, introspect to get the type and
#   the error message. Append the child stack trace as a string to the error
#   message. Raise another exception of the same type, with the appended error
#   message.
