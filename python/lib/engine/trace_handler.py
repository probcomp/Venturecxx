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

The WorkerProcess classes are subclasses of either multiprocessing.Process for
multiprocessing, or multiprocessing.dummy.Process for threading, or
SynchronousBase (this module) for synchronous operation.

Each instance of WorkerProcess contains a list of states (which are always
Traces in this use case, but WorkerProcess doesn't care), and
interacts with the underlying object by forwarding method calls.
As a subclass of Process, each
instance has a run() method. The run() method is simply a listener; the
WorkerProcess waits for commands sent over the pipe from the TraceHandler
(described below), calls the method associated with the command, and then
returns the result to the Handler over the pipe. All methods are wrapped in
the @safely decorator, whose purpose is to catch all errors occurring in workers
and return them over the Pipe, to be raised by the Handler. This prevents
exceptions in the child processes from hanging the program.
The WorkerProcess classes are daemonic; the TraceHandler need not wait for
the run() methods of its children to complete before regaining control of
the program. Also as daemonic processes, all WorkerProcess instances will
be terminated when the controlling Handler is deleted.
For more information on the WorkerProcess class hierarchy, see the docstrings
below.

The TraceHandler classes facilitate communication between the Engine and the
individual WorkerProcess instances. Each TraceHandler stores a list of
WorkerProcesses, and also a list of Pipes interacting with those
WorkerProcesses, as attributes.
When the Engine calls a method (say, engine.assume()), the TraceHandler passes
this command over the Pipes to the WorkerProcesses via its "delegate" method,
and then waits for results to be returned from the workers. It regains control
of the program when all results have been returned. It then checks for
exceptions; if any are found, it re-raises the first one. Else it passes its
result back to the Engine.
The TraceHandler also has methods to retrieve serialized traces from the
individual WorkerProcesses and reconstruct them. For the MultiprocessingTraceHandler,
Traces must be serialized before being sent from WorkerProcesses back to the
Handler. This is the case since Trace objects are not picklable and hence
cannot be sent over Pipes directly.
For more information on the TraceHandler class hierarchy, see the docstrings
below.
'''

import multiprocessing as mp
from multiprocessing import dummy as mpd
from sys import exc_info
from traceback import format_exc
import random
import numpy as np

from venture.exception import VentureException, format_worker_trace

######################################################################
# Auxiliary functions for safe function evaluation
######################################################################

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
  def __init__(self, traces, rng_style, process_cap):
    """A TraceHandler maintains:

    - An array of objects representing the worker processes.

    - An array of the local ends of pipes for talking to them.

    - Each child process manages a chunk of the traces.  The full set
      of traces is notionally the concatenation of all the chunks, in
      the order given by the array of child processes.

    - To be able to interact with a single trace, the TraceHandler
      also maintains a mapping between the index in the total trace
      list and (the chunk that trace is part of and its offset in that
      chunk).

    """
    self.rng_style = rng_style
    self.process_cap = process_cap
    self.processes = []
    self.pipes = []  # Parallel to processes
    self.chunk_sizes = [] # Parallel to processes
    self.chunk_indexes = [] # One per trace
    self.chunk_offsets = [] # Parallel to chunk_indexes
    self._create_processes(traces)
    self.reset_seeds()

  def __del__(self):
    # stop child processes
    self.delegate('stop')

  def _create_processes(self, traces):
    Pipe, WorkerProcess = self._pipe_and_process_types()
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
      process = WorkerProcess(traces[chunk_start:chunk_end], child, self.rng_style)
      process.start()
      self.pipes.append(parent)
      self.processes.append(process)
      self.chunk_sizes.append(chunk_end - chunk_start)
      for i in range (chunk_end - chunk_start):
        self.chunk_indexes.append(chunk)
        self.chunk_offsets.append(i)

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
      exception_handler = WorkerProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one_chunk(self, ix, cmd, *args, **kwargs):
    '''Delegate command to (all the traces of) a single worker, indexed by ix in the process list'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs, None))
    res = pipe.recv()
    if any([threw_error(entry) for entry in res]):
      exception_handler = WorkerProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single trace, indexed by ix in the trace list'''
    pipe = self.pipes[self.chunk_indexes[ix]]
    pipe.send((cmd, args, kwargs, self.chunk_offsets[ix]))
    res = pipe.recv()
    if threw_error(res):
      exception_handler = WorkerProcessExceptionHandler([res])
      raise exception_handler.gen_exception()
    return res

  def delegate_distinguished(self, cmd, *args, **kwargs):
    return self.delegate_one(0, cmd, *args, **kwargs)

  def can_retrieve_state(self):
    """In general, the short-circuit offered by SharedMemoryHandlerBase is not available."""
    return False

# Base class short-cutting around serialization if the memory is shared

class SharedMemoryHandlerBase(HandlerBase):
  '''Offers the client a short-circuit for retrieving the managed
  states without having to serialize them.

  This harmlessly saves effort if the states are actually in a shared
  memory space (i.e., multiprocessing.dummy or completely synchronous)
  and we are not trying to debug serialization.  Inherited by
  ThreadedTraceHandler and SynchronousTraceHandler.

  '''

  def can_retrieve_state(self): return True

  def retrieve_state(self, ix):
    return self.delegate_one(ix, 'send_state')

  def retrieve_states(self):
    return self.delegate('send_state')

######################################################################
# Concrete trace handlers

class MultiprocessingTraceHandler(HandlerBase):
  '''Controls MultiprocessingWorkerProcesses. Communicates with workers
  via multiprocessing.Pipe. Truly multiprocess implementation.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mp.Pipe, MultiprocessingWorkerProcess

class ThreadedSerializingTraceHandler(HandlerBase):
  '''Controls ThreadedSerializingWorkerProcesses. Communicates with
  workers via multiprocessing.dummy.Pipe. Do not use for actual
  modeling. Rather, intended for debugging; API mimics
  MultiprocessingTraceHandler, but implementation is multithreaded.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedSerializingWorkerProcess

class ThreadedTraceHandler(SharedMemoryHandlerBase):
  '''Controls ThreadedWorkerProcesses. Communicates via
  multiprocessing.dummy.Pipe. Do not use for actual modeling. Rather,
  intended for debugging multithreading; API mimics
  ThreadedSerializingTraceHandler, but does not serialize the traces.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedWorkerProcess

class SynchronousSerializingTraceHandler(HandlerBase):
  '''Controls SynchronousSerializingWorkerProcesses. Communicates via
  SynchronousPipe. Do not use for actual modeling. Rather, intended
  for debugging multithreading; API mimics
  MultiprocessingTraceHandler, but runs synchronously in one thread.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousSerializingWorkerProcess

class SynchronousTraceHandler(SharedMemoryHandlerBase):
  '''Controls SynchronousWorkerProcesses. Default
  TraceHandler. Communicates via SynchronousPipe.  This is what you
  want if you don't want to pay for parallelism.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousWorkerProcess

######################################################################
# Per-process workers; interact with individual instances of the state
######################################################################

class Safely(object):
  """Wraps "safely" around all the methods of the argument.

  """
  def __init__(self, obj): self.obj = obj

  def __getattr__(self, attrname):
    # @safely doesn't work as a decorator here; do it this way.
    return safely(safely(getattr)(self.obj, attrname))


class ProcessBase(object):

  '''The base class is ProcessBase, which manages a list of instances of
  the state synchronously (using Safely objects to catch exceptions).

  '''
  def __init__(self, states, pipe, rng_style):
    self.states = [Safely(s) for s in states]
    self.pipe = pipe
    self.rng_style = rng_style
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
      res = getattr(self.states[index], cmd)(*args, **kwargs)
    else:
      res = [getattr(s, cmd)(*args, **kwargs) for s in self.states]
    self.pipe.send(res)

  @safely
  def set_seeds(self, _index, seeds):
    # If we're in puma, set the seed; else don't.
    # The truly parallel case is handled by the subclass MultiprocessingWorkerProcess.
    if self.rng_style == 'local':
      for (state, seed) in zip(self.states, seeds):
        state.set_seed(seed)
    return [None for _ in self.states]

  def send_state(self, _index):
    raise VentureException("fatal", "Cannot transmit state directly if memory is not shared")

######################################################################
# Base classes defining how to send states, and process types

class SharedMemoryProcessBase(ProcessBase):
  '''Offers a short-cut around serialization by sending states directly.

  Only works if the memory space is shared between worker and master,
  and we are not trying to emulate the separate-memory regime.
  Inherited by ThreadedWorkerProcess and SynchronousWorkerProcess.

  '''
  @safely
  def send_state(self, index):
    if index is not None:
      return self.states[index].obj
    else:
      return [s.obj for s in self.states]

class MultiprocessBase(mp.Process):
  '''
  Specifies multiprocess implementation; inherited by MultiprocessingWorkerProcess.
  '''
  def _initialize(self):
    mp.Process.__init__(self)
    self.daemon = True

class ThreadingBase(mpd.Process):
  '''
  Specifies threaded implementation; inherited by ThreadedSerializingWorkerProcess
  and ThreadedWorkerProcess.
  '''
  def _initialize(self):
    mpd.Process.__init__(self)
    self.daemon = True

class SynchronousBase(object):
  '''Specifies synchronous implementation; inherited by
  SynchronousSerializingWorkerProcess and SynchronousWorkerProcess.
  '''
  def _initialize(self):
    self.pipe.register_callback(self.poll)

  def start(self): pass

######################################################################
# Concrete process classes

# pylint: disable=too-many-ancestors
class MultiprocessingWorkerProcess(ProcessBase, MultiprocessBase):
  '''
  True parallelism via multiprocessing. Controlled by MultiprocessingTraceHandler.
  '''
  @safely
  def set_seeds(self, index, seeds):
    # override the default set_seeds method; if we're in parallel Python,
    # reset the global random seeds.
    if self.rng_style == 'process':
      # In Python the RNG is global; only need to set it once.
      random.seed(seeds[0])
      np.random.seed(seeds[0])
      return [None for _ in self.states]
    else:
      return ProcessBase.set_seeds(self, index, seeds)

class ThreadedSerializingWorkerProcess(ProcessBase, ThreadingBase):
  '''Emulates MultiprocessingWorkerProcess by serializing the managed states, but
  is implemented with threading. Could be useful for debugging?
  Controlled by ThreadedSerializingTraceHandler.

  '''
  pass

class ThreadedWorkerProcess(SharedMemoryProcessBase, ThreadingBase):
  '''Emulates MultiprocessingWorkerProcess by running multithreaded but
  without serializing states.  Could be useful for debugging?
  Controlled by ThreadedTraceHandler.

  '''
  pass

class SynchronousSerializingWorkerProcess(ProcessBase, SynchronousBase):
  '''Emulates MultiprocessingWorkerProcess by serializing the states as
  it would, while still running in one thread.  Use for debugging.
  Controlled by SynchronousSerializingTraceHandler.

  '''
  pass

class SynchronousWorkerProcess(SharedMemoryProcessBase, SynchronousBase):
  '''
  Default. Keeps everything synchronous. Controlled by
  SynchronousTraceHandler.
  '''
  pass

######################################################################
# Code to handle exceptions in worker processes
######################################################################

class WorkerProcessExceptionHandler(object):
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
