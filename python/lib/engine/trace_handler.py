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
individual TraceProcesses and reconstruct them. For the MultiprocessingTraceHandler,
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
import venture.lite.foreign as foreign

######################################################################
# Auxiliary functions for trace serialization and safe function evaluation
######################################################################

def dump_trace(trace, directives, skipStackDictConversion=False):
  # TODO: It would be good to pass foreign_sps to this function as well,
  # and then check that the passed foreign_sps match up with the foreign
  # SP's bound in the trace's global environment. However, in the Puma backend
  # there is currently no way to access this global environment.
  # This block mutates the trace
  db = trace.makeSerializationDB()
  for did, directive in sorted(directives.items(), reverse=True):
    if directive[0] == "observe":
      trace.unobserve(did)
    trace.unevalAndExtract(did, db)

  # This block undoes the mutation on the trace done by the previous block; but
  # it does not destroy the value stack because the actual OmegaDB (superclass
  # of OrderedOmegaDB) has the values.
  for did, directive in sorted(directives.items()):
    trace.restore(did, db)
    if directive[0] == "observe":
      trace.observe(did, directive[2])

  # TODO Actually, I should restore the degree of incorporation the
  # original trace had.  In the absence of tracking that, this
  # heuristically makes the trace fully incorporated.  Hopefully,
  # mistakes will be rarer than in the past (which will make them even
  # harder to detect).
  trace.makeConsistent()

  return trace.dumpSerializationDB(db, skipStackDictConversion)

def restore_trace(trace, directives, values, foreign_sps,
                  backend, skipStackDictConversion=False):
  # bind the foreign sp's; wrap if necessary
  for name, sp in foreign_sps.items():
    if backend != 'lite':
      sp = foreign.ForeignLiteSP(sp)
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
  behavior in parallel, threaded, and sequential modes to be defined by subclasses.
  '''
  __metaclass__ = ABCMeta
  def __init__(self, traces, backend, process_cap):
    """A TraceHandler maintains:

    - An array of (logspace) weights of the traces being managed.  (It
      seems reasonable to keep the weights on the master process, for
      ease of access.)

    - Two parallel arrays: child process objects, and the local ends
      of pipes for talking to them.

    - Each child process manages a chunk of the traces.  The full set
      of traces is notionally the concatenation of all the chunks, in
      the order given by the array of child processes.

    - To be able to interact with a single trace, the TraceHandler
      also maintains a mapping between the index in the total trace
      list and (the chunk that trace is part of and its offset in that
      chunk).

    """
    self.backend = backend
    self.process_cap = process_cap
    self.processes = []
    self.pipes = []  # Parallel to processes
    self.chunk_sizes = [] # Parallel to processes
    self.log_weights = []
    self.chunk_indexes = [] # Parallel to log_weights
    self.chunk_offsets = [] # Parallel to chunk_indexes
    self._create_processes(traces)
    self.reset_seeds()

  def __del__(self):
    # stop child processes
    self.delegate('stop')

  def _create_processes(self, traces):
    Pipe, TraceProcess = self._pipe_and_process_types()
    if self.process_cap is None:
      base_size = 1
      extras = 0
      chunk_ct = len(traces)
    else:
      (base_size, extras) = divmod(len(traces), self.process_cap)
      chunk_ct = min(self.process_cap, len(traces))
    for chunk in range(chunk_ct):
      parent, child = Pipe()
      if chunk < extras:
        chunk_start = chunk * (base_size + 1)
        chunk_end = chunk_start + base_size + 1
      else:
        chunk_start = extras + chunk * base_size
        chunk_end = chunk_start + base_size
      assert chunk_end <= len(traces) # I think I wrote this code to ensure this
      process = TraceProcess(traces[chunk_start:chunk_end], child, self.backend)
      process.start()
      self.pipes.append(parent)
      self.processes.append(process)
      self.chunk_sizes.append(chunk_end - chunk_start)
      for i in range (chunk_end - chunk_start):
        self.log_weights.append(0)
        self.chunk_indexes.append(chunk)
        self.chunk_offsets.append(i)

  def incorporate(self):
    weight_increments = self.delegate('makeConsistent')
    for i, increment in enumerate(weight_increments):
      self.log_weights[i] += increment

  def likelihood_weight(self):
    self.log_weights = self.delegate('likelihood_weight')

  def reset_seeds(self):
    for i in range(len(self.processes)):
      self.delegate_one_chunk(i, 'set_seeds', [random.randint(1,2**31-1) for _ in range(self.chunk_sizes[i])])

  # NOTE: I could metaprogram all the methods that delegate passes on,
  # but it feels cleaner just call the delegator than to add another level
  # of wrapping
  def delegate(self, cmd, *args, **kwargs):
    '''Delegate command to all workers'''
    # send command
    for pipe in self.pipes: pipe.send((cmd, args, kwargs, None))
    if cmd == 'stop': return
    res = []
    for pipe in self.pipes:
      ans = pipe.recv()
      res.extend(ans)
    if any([threw_error(entry) for entry in res]):
      exception_handler = TraceProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one_chunk(self, ix, cmd, *args, **kwargs):
    '''Delegate command to (all the traces of) a single worker, indexed by ix in the process list'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs, None))
    res = pipe.recv()
    if any([threw_error(entry) for entry in res]):
      exception_handler = TraceProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single trace, indexed by ix in the trace list'''
    pipe = self.pipes[self.chunk_indexes[ix]]
    pipe.send((cmd, args, kwargs, self.chunk_offsets[ix]))
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
# Base classes serializing traces properly

class SerializingHandlerArchitecture(HandlerBase):
  '''
  Retrieves traces by requesting dumps from workers and reconstructing on
  other end of Pipe. Inherited by MultiprocessingTraceHandler (for which this mode
  of communication is required) and ThreadedSerializingTraceHandler (which is sequential
  but mimics the API of the Parallel version).
  '''
  def retrieve_trace(self, ix, engine):
    dumped = self.retrieve_dump(ix, engine)
    return engine.restore_trace(dumped)

  def retrieve_traces(self, engine):
    dumped_all = self.retrieve_dumps(engine)
    return [engine.restore_trace(dumped) for dumped in dumped_all]

class SharedMemoryHandlerArchitecture(HandlerBase):
  '''
  Retrieves traces by requesting the traces themselves directly. Since
  multiprocessing.dummy is actually just a wrapper around Threading, there is
  no problem with sending arbitrary Python objects over dummy.Pipes. Inherited
  by ThreadedTraceHandler.
  '''
  def retrieve_trace(self, ix, engine):
    return self.delegate_one(ix, 'send_trace')

  def retrieve_traces(self, engine):
    return self.delegate('send_trace')

######################################################################
# Concrete trace handlers

class MultiprocessingTraceHandler(SerializingHandlerArchitecture):
  '''Controls MultiprocessingTraceProcesses. Communicates with workers
  via multiprocessing.Pipe. Truly multiprocess implementation.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mp.Pipe, MultiprocessingTraceProcess

class ThreadedSerializingTraceHandler(SerializingHandlerArchitecture):
  '''Controls ThreadedSerializingTraceProcesses. Communicates with
  workers via multiprocessing.dummy.Pipe. Do not use for actual
  modeling. Rather, intended for debugging; API mimics
  MultiprocessingTraceHandler, but implementation is multithreaded.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedSerializingTraceProcess

class ThreadedTraceHandler(SharedMemoryHandlerArchitecture):
  '''Controls ThreadedTraceProcesses. Communicates via
  multiprocessing.dummy.Pipe. Do not use for actual modeling. Rather,
  intended for debugging multithreading; API mimics
  ThreadedSerializingTraceHandler, but does not serialize the traces.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedTraceProcess

class SynchronousSerializingTraceHandler(SerializingHandlerArchitecture):
  '''Controls SynchronousSerializingTraceProcesses. Communicates via
  SynchronousPipe. Do not use for actual modeling. Rather, intended
  for debugging multithreading; API mimics
  MultiprocessingTraceHandler, but runs synchronously in one thread.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousTraceProcess

class SynchronousTraceHandler(SharedMemoryHandlerArchitecture):
  '''Controls SynchronousTraceProcesses. Default
  TraceHandler. Communicates via SynchronousPipe.  This is what you
  want if you don't want to pay for parallelism.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousTraceProcess

######################################################################
# Trace processes; interact with individual traces
######################################################################

class TraceWrapper(object):
  """Defines all the methods that do the actual work of interacting with
  traces.

  """
  def __init__(self, trace): self.trace = trace

  def __getattr__(self, attrname):
    # if attrname isn't attribute of TraceWrapper, look for it as a
    # method on the trace.  Safely doesn't work as a decorator here;
    # do it this way.
    return safely(safely(getattr)(self.trace, attrname))

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
      d = expToDict(exp)
      #import pdb; pdb.set_trace()
      self.trace.infer(d)


class ProcessBase(object):

  '''The base class is ProcessBase, which manages a list of traces
  (through TraceWrapper objects).

  '''
  __metaclass__ = ABCMeta
  def __init__(self, traces, pipe, backend):
    self.traces = [TraceWrapper(t) for t in traces]
    self.pipe = pipe
    self.backend = backend
    self._initialize()

  def run(self):
    while True: self.poll()

  def poll(self):
    cmd, args, kwargs, index = self.pipe.recv()
    if cmd == 'stop':
      return
    if hasattr(self, cmd):
      res = getattr(self, cmd)(index, *args, **kwargs)
    elif index is not None:
      res = getattr(self.traces[index], cmd)(*args, **kwargs)
    else:
      res = [getattr(t, cmd)(*args, **kwargs) for t in self.traces]
    self.pipe.send(res)

  @safely
  def set_seeds(self, _index, seeds):
    # if we're in puma or we're truly parallel, set the seed; else don't.
    if self.backend == 'puma':
      for (t, s) in zip(self.traces, seeds):
        t.set_seed(s)
    return [None for _ in self.traces]

  @abstractmethod
  def send_trace(self, index): pass

  @safely
  def send_dump(self, index, directives):
    if index is not None:
      return dump_trace(self.traces[index].trace, directives)
    else:
      return [dump_trace(t.trace, directives) for t in self.traces]

######################################################################
# Base classes defining how to send traces, and process types

class SerializingProcessArchitecture(ProcessBase):
  '''
  Attempting to send a trace without first serializing results in an exception.
  Inherited by MultiprocessingTraceProcess (for which this behavior is necessary) and
  ThreadedSerializingTraceProcess (which mimics the API of the Parallel process).
  '''
  @safely
  def send_trace(self, _index):
    raise VentureException("fatal",
                           "Must serialize traces before sending in parallel architecture")

class SharedMemoryProcessArchitecture(ProcessBase):
  '''
  Sends traces directly. Inherited by ThreadedTraceProcess.
  '''
  @safely
  def send_trace(self, index):
    if index is not None:
      return self.traces[index].trace
    else:
      return [t.trace for t in self.traces]

class MultiprocessBase(mp.Process):
  '''
  Specifies multiprocess implementation; inherited by MultiprocessingTraceProcess.
  '''
  def _initialize(self):
    mp.Process.__init__(self)
    self.daemon = True

class ThreadingBase(mpd.Process):
  '''
  Specifies threaded implementation; inherited by ThreadedSerializingTraceProcess
  and ThreadedTraceProcess.
  '''
  def _initialize(self):
    mpd.Process.__init__(self)
    self.daemon = True

class SynchronousBase(object):
  '''Specifies synchronous implementation; inherited by
  SynchronousSerializingTraceProcess and SynchronousTraceProcess.
  '''
  def _initialize(self):
    self.pipe.register_callback(self.poll)

  def start(self): pass

######################################################################
# Concrete process classes

# pylint: disable=too-many-ancestors
class MultiprocessingTraceProcess(SerializingProcessArchitecture, MultiprocessBase):
  '''
  True parallel traces via multiprocessing. Controlled by MultiprocessingTraceHandler.
  '''
  @safely
  def set_seeds(self, index, seeds):
    # override the default set_seeds method; if we're in parallel Python,
    # reset the global random seeds.
    if self.backend == 'lite':
      # In Python the RNG is global; only need to set it once.
      random.seed(seeds[0])
      np.random.seed(seeds[0])
      return [None for _ in self.traces]
    else:
      return ProcessBase.set_seeds(self, index, seeds)

class ThreadedSerializingTraceProcess(SerializingProcessArchitecture, ThreadingBase):
  '''Emulates MultiprocessingTraceProcess by serializing the traces, but
  is implemented with threading. Could be useful for debugging?
  Controlled by ThreadedSerializingTraceHandler.

  '''
  pass

class ThreadedTraceProcess(SharedMemoryProcessArchitecture, ThreadingBase):
  '''Emulates MultiprocessingTraceProcess by running multithreaded but
  without serializing traces.  Could be useful for debugging?
  Controlled by ThreadedTraceHandler.

  '''
  pass

class SynchronousSerializingTraceProcess(SerializingProcessArchitecture, SynchronousBase):
  '''Emulates MultiprocessingTraceProcess by serializing the traces as
  it would, while still running in one thread.  Use for debugging.
  Controlled by SynchronousSerializingTraceHandler.

  '''
  pass

class SynchronousTraceProcess(SharedMemoryProcessArchitecture, SynchronousBase):
  '''
  Default class for interacting with Traces. Controlled by
  SynchronousTraceHandler.
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
      msg = (str(self.values[0].message) + format_worker_trace(self.traces[0]))
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

######################################################################
# Fake Pipes that actually just use one thread
######################################################################

class SynchronousOneWayPipe(object):
  def __init__(self):
    self.other = None
    self.objs = []
    self.cbs = []

  def register_callback(self, cb):
    self.cbs.append(cb)

  def send(self, obj):
    self.other.emplace(obj)

  def emplace(self, obj):
    self.objs.append(obj)
    for cb in self.cbs:
      cb()

  def recv(self):
    ans = self.objs[0]
    self.objs = self.objs[1:]
    return ans

def SynchronousPipe():
  parent = SynchronousOneWayPipe()
  child = SynchronousOneWayPipe()
  parent.other = child
  child.other = parent
  return (parent, child)

class SynchronousProcess(object):
  pass
