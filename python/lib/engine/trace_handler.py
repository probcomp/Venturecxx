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

'''Generic multiprocessing support for mapping methods over a set of (stateful) objects.

In Venture, this is used to support parallelism across multiple
execution histories ("particles") of the model program.

The architecture is as follows:

The WorkerProcess classes are subclasses of either
multiprocessing.Process for multiprocessing, or
multiprocessing.dummy.Process for threading, or SynchronousBase (in
this module) for synchronous operation.

Each instance of WorkerProcess contains a list of objects (which are
always Traces in this use case, but WorkerProcess doesn't care), and
interacts with each underlying object by forwarding method calls.  As
a subclass of Process, each instance has a run() method. The run()
method is simply a listener; the WorkerProcess waits for commands sent
over the pipe from the Master (described below), calls the method
associated with the command, and then returns the result to the Master
over the pipe. All methods are wrapped in the @safely decorator, whose
purpose is to catch all errors occurring in workers and return them
over the Pipe, to be raised by the Master in the master process. This
prevents exceptions in the child processes from hanging the program.

The WorkerProcess classes are daemonic; the Master need not wait for
the run() methods of its children to complete before regaining control
of the program. Also as daemonic processes, all WorkerProcess
instances will be terminated when the controlling Master is deleted.
For more information on the WorkerProcess class hierarchy, see the
docstrings below.

The Master classes facilitate communication between the client and the
individual WorkerProcess instances. Each Master stores a list of
WorkerProcesses, and also a list of Pipes interacting with those
WorkerProcesses, as attributes.  When the client wants something done,
it calls "delegate" (or "delegate_one" for interacting with just one
controlled object) on the Master. The Master then passes this command
over the Pipes to the WorkerProcesses, and waits for results to be
returned from the workers. It regains control of the program when all
results have been returned. It then checks for exceptions; if any are
found, it re-raises the first one. Else it passes its result back to
the client.

This Master/Worker system has a facility for setting the random seeds
on the workers.  This respects a flag for whether the objects being
managed have their own random states (which should then be settable
with the set_seed method), or rely on the process-global Python PRNG
available in each child process.

For more information on the Master class hierarchy, see the docstrings
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
# The masters; manage communication between the client and the objects
######################################################################

class MasterBase(object):
  '''Base class for all Masters.

  Defines the majority of the methods to interact with the Masters.
  Subclassed to generate different behavior in parallel, threaded, and
  sequential modes.

  '''
  def __init__(self, objects, rng_style, process_cap):
    """A Master maintains:

    - An array of objects representing the worker processes.

    - An array of the local ends of pipes for talking to them.

    - Each child process manages a chunk of the objects.  The full set
      of objects is notionally the concatenation of all the chunks, in
      the order given by the array of child processes.

    - To be able to interact with a single object, the Master
      also maintains a mapping between the index in the total object
      list and (the chunk that object is part of and its offset in that
      chunk).

    """
    self.rng_style = rng_style
    self.process_cap = process_cap
    self.processes = []
    self.pipes = []  # Parallel to processes
    self.chunk_sizes = [] # Parallel to processes
    self.chunk_indexes = [] # One per object
    self.chunk_offsets = [] # Parallel to chunk_indexes
    self._create_processes(objects)
    self.reset_seeds()

  def __del__(self):
    # stop child processes
    self.delegate('stop')

  def _create_processes(self, objects):
    Pipe, WorkerProcess = self._pipe_and_process_types()
    if self.process_cap is None:
      base_size = 1
      extras = 0
      chunk_ct = len(objects)
    else:
      (base_size, extras) = divmod(len(objects), self.process_cap)
      chunk_ct = min(self.process_cap, len(objects))
    for chunk in range(chunk_ct):
      parent, child = Pipe()
      if chunk < extras:
        chunk_start = chunk * (base_size + 1)
        chunk_end = chunk_start + base_size + 1
      else:
        chunk_start = extras + chunk * base_size
        chunk_end = chunk_start + base_size
      assert chunk_end <= len(objects) # I think I wrote this code to ensure this
      process = WorkerProcess(objects[chunk_start:chunk_end], child, self.rng_style)
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
    '''Delegate command to (all the objects of) a single worker, indexed by ix in the process list'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs, None))
    res = pipe.recv()
    if any([threw_error(entry) for entry in res]):
      exception_handler = WorkerProcessExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def delegate_one(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single object, indexed by ix in the object list'''
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
    """In general, the short-circuit offered by SharedMemoryMasterBase is not available."""
    return False

# Base class short-cutting around serialization if the memory is shared

class SharedMemoryMasterBase(MasterBase):
  '''Offers the client a short-circuit for retrieving the managed
  objects without having to serialize them.

  This harmlessly saves effort if the objects are actually in a shared
  memory space (i.e., multiprocessing.dummy or completely synchronous)
  and we are not trying to debug serialization.  Inherited by
  ThreadedMaster and SynchronousMaster.

  '''

  def can_retrieve_state(self): return True

  def retrieve_state(self, ix):
    return self.delegate_one(ix, 'send_state')

  def retrieve_states(self):
    return self.delegate('send_state')

######################################################################
# Concrete masters

class MultiprocessingMaster(MasterBase):
  '''Controls MultiprocessingWorkerProcesses. Communicates with workers
  via multiprocessing.Pipe. Truly multiprocess implementation.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mp.Pipe, MultiprocessingWorkerProcess

class ThreadedSerializingMaster(MasterBase):
  '''Controls ThreadedSerializingWorkerProcesses. Communicates with
  workers via multiprocessing.dummy.Pipe. Do not use for actual
  modeling. Rather, intended for debugging; API mimics
  MultiprocessingMaster, but implementation is multithreaded.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedSerializingWorkerProcess

class ThreadedMaster(SharedMemoryMasterBase):
  '''Controls ThreadedWorkerProcesses. Communicates via
  multiprocessing.dummy.Pipe. Do not use for actual modeling. Rather,
  intended for debugging multithreading; API mimics
  ThreadedSerializingMaster, but permits the shared-memory shortcut
  around serialization.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedWorkerProcess

class SynchronousSerializingMaster(MasterBase):
  '''Controls SynchronousSerializingWorkerProcesses. Communicates via
  SynchronousPipe. Do not use for actual modeling. Rather, intended
  for debugging multiprocessing; API mimics
  MultiprocessingMaster, but runs synchronously in one thread.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousSerializingWorkerProcess

class SynchronousMaster(SharedMemoryMasterBase):
  '''Controls SynchronousWorkerProcesses. Default
  Master. Communicates via SynchronousPipe.  This is what you
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

  '''The base class is ProcessBase, which manages a list of objects
  synchronously (using Safely objects to catch exceptions).

  '''
  def __init__(self, objs, pipe, rng_style):
    self.objs = [Safely(o) for o in objs]
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
      res = getattr(self.objs[index], cmd)(*args, **kwargs)
    else:
      res = [getattr(o, cmd)(*args, **kwargs) for o in self.objs]
    self.pipe.send(res)

  @safely
  def set_seeds(self, _index, seeds):
    # If we're in puma, set the seed; else don't.
    # The truly parallel case is handled by the subclass MultiprocessingWorkerProcess.
    if self.rng_style == 'local':
      for (obj, seed) in zip(self.objs, seeds):
        obj.set_seed(seed)
    return [None for _ in self.objs]

  def send_state(self, _index):
    raise VentureException("fatal", "Cannot transmit object directly if memory is not shared")

######################################################################
# Base classes defining how to send states, and process types

class SharedMemoryProcessBase(ProcessBase):
  '''Offers a short-cut around serialization by sending objects directly.

  Only works if the memory space is shared between worker and master,
  and we are not trying to emulate the separate-memory regime.
  Inherited by ThreadedWorkerProcess and SynchronousWorkerProcess.

  '''
  @safely
  def send_state(self, index):
    if index is not None:
      return self.objs[index].obj
    else:
      return [o.obj for o in self.objs]

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
  True parallelism via multiprocessing. Controlled by MultiprocessingMaster.
  '''
  @safely
  def set_seeds(self, index, seeds):
    # override the default set_seeds method; if we're in parallel Python,
    # reset the global random seeds.
    if self.rng_style == 'process':
      # In Python the RNG is global; only need to set it once.
      random.seed(seeds[0])
      np.random.seed(seeds[0])
      return [None for _ in self.objs]
    else:
      return ProcessBase.set_seeds(self, index, seeds)

class ThreadedSerializingWorkerProcess(ProcessBase, ThreadingBase):
  '''Emulates MultiprocessingWorkerProcess by forbidding the short-cut
  around serializing the managed objects, but is implemented with
  threading. Could be useful for debugging?  Controlled by
  ThreadedSerializingMaster.

  '''
  pass

class ThreadedWorkerProcess(SharedMemoryProcessBase, ThreadingBase):
  '''Emulates MultiprocessingWorkerProcess by running multithreaded, but
  permits the shared-memory shortcut around serialization.  Could be
  useful for debugging?  Controlled by ThreadedMaster.

  '''
  pass

class SynchronousSerializingWorkerProcess(ProcessBase, SynchronousBase):
  '''Emulates MultiprocessingWorkerProcess by forbidding the
  serialization short-cut as it would, while still running in one
  thread.  Use for debugging.  Controlled by
  SynchronousSerializingMaster.

  '''
  pass

class SynchronousWorkerProcess(SharedMemoryProcessBase, SynchronousBase):
  '''Default. Keeps everything synchronous, and short-cuts around
  serialization. Controlled by SynchronousMaster.

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

# Concerning the hack above: In designing masters that handle parallel objects,
# we'd like errors in the child trace process to be passed back up to the master.
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
