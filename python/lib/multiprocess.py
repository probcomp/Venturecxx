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

'''Generic multiprocessing support for mapping methods over a set of (stateful) objects.

In Venture, this is used to support parallelism across multiple
execution histories ("particles") of the model program.

The architecture is as follows:

The Worker classes are subclasses of either
multiprocessing.Process for multiprocessing, or
multiprocessing.dummy.Process for threading, or SynchronousBase (in
this module) for synchronous operation.

Each instance of Worker contains a list of objects (which are
always Traces in this use case, but Worker doesn't care), and
interacts with each underlying object by forwarding method calls.  As
a subclass of Process, each instance has a run() method. The run()
method is simply a listener; the Worker waits for commands sent
over the pipe from the Master (described below), calls the method
associated with the command, and then returns the result to the Master
over the pipe. All methods are wrapped in the @safely decorator, whose
purpose is to catch all errors occurring in workers and return them
over the Pipe, to be raised by the Master in the master process. This
prevents exceptions in the child processes from hanging the program.

The Worker classes are daemonic; the Master need not wait for
the run() methods of its children to complete before regaining control
of the program. Also as daemonic processes, all Worker
instances will be terminated when the controlling Master is deleted.
For more information on the Worker class hierarchy, see the
docstrings below.

The Master classes facilitate communication between the client and the
individual Worker instances. Each Master stores a list of
Workers, and also a list of Pipes interacting with those
Workers, as attributes.  When the client wants something done,
it calls "map" (or "at" for interacting with just one
controlled object) on the Master. The Master then passes this command
over the Pipes to the Workers, and waits for results to be
returned from the workers. It regains control of the program when all
results have been returned. It then checks for exceptions; if any are
found, it re-raises the first one. Else it passes its result back to
the client.

This Master/Worker system has a facility for setting the random seeds
on the workers.  This respects the possibility that each object may
have a local PRNG as follows: When the Master issues a seed reset, if
an object defines a "has_own_prng" method, and that method returns
"True", then the Worker will try to set its PRNG seed by calling its
"set_seed" method.  If not, the Worker will assume the object relies
on the process-global Python PRNG available in each child process.

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
  def __init__(self, objects, process_cap):
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
    self.map('stop')

  def _create_processes(self, objects):
    Pipe, Worker = self._pipe_and_process_types()
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
      process = Worker(objects[chunk_start:chunk_end], child)
      process.start()
      self.pipes.append(parent)
      self.processes.append(process)
      self.chunk_sizes.append(chunk_end - chunk_start)
      for i in range (chunk_end - chunk_start):
        self.chunk_indexes.append(chunk)
        self.chunk_offsets.append(i)

  def reset_seeds(self):
    for i in range(len(self.processes)):
      self.map_chunk(i, 'set_seeds', [random.randint(1,2**31-1) for _ in range(self.chunk_sizes[i])])

  def map(self, cmd, *args, **kwargs):
    '''Delegate command to all workers'''
    # send command
    for pipe in self.pipes: pipe.send((cmd, args, kwargs, None))
    if cmd == 'stop': return
    res = []
    for pipe in self.pipes:
      ans = pipe.recv()
      res.extend(ans)
    if any([threw_error(entry) for entry in res]):
      exception_handler = WorkerExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def map_chunk(self, ix, cmd, *args, **kwargs):
    '''Delegate command to (all the objects of) a single worker, indexed by ix in the process list'''
    pipe = self.pipes[ix]
    pipe.send((cmd, args, kwargs, None))
    res = pipe.recv()
    if any([threw_error(entry) for entry in res]):
      exception_handler = WorkerExceptionHandler(res)
      raise exception_handler.gen_exception()
    return res

  def at(self, ix, cmd, *args, **kwargs):
    '''Delegate command to a single object, indexed by ix in the object list'''
    pipe = self.pipes[self.chunk_indexes[ix]]
    pipe.send((cmd, args, kwargs, self.chunk_offsets[ix]))
    res = pipe.recv()
    if threw_error(res):
      exception_handler = WorkerExceptionHandler([res])
      raise exception_handler.gen_exception()
    return res

  def at_distinguished(self, cmd, *args, **kwargs):
    return self.at(0, cmd, *args, **kwargs)

  def can_shortcut_retrieval(self):
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

  def can_shortcut_retrieval(self): return True

  def retrieve(self, ix):
    return self.at(ix, 'send_object')

  def retrieve_all(self):
    return self.map('send_object')

######################################################################
# Concrete masters

class MultiprocessingMaster(MasterBase):
  '''Controls MultiprocessingWorkers. Communicates with workers
  via multiprocessing.Pipe. Truly multiprocess implementation.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mp.Pipe, MultiprocessingWorker

class ThreadedSerializingMaster(MasterBase):
  '''Controls ThreadedSerializingWorkers. Communicates with
  workers via multiprocessing.dummy.Pipe. Do not use for actual
  modeling. Rather, intended for debugging; API mimics
  MultiprocessingMaster, but implementation is multithreaded.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedSerializingWorker

class ThreadedMaster(SharedMemoryMasterBase):
  '''Controls ThreadedWorkers. Communicates via
  multiprocessing.dummy.Pipe. Do not use for actual modeling. Rather,
  intended for debugging multithreading; API mimics
  ThreadedSerializingMaster, but permits the shared-memory shortcut
  around serialization.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return mpd.Pipe, ThreadedWorker

class SynchronousSerializingMaster(MasterBase):
  '''Controls SynchronousSerializingWorkers. Communicates via
  SynchronousPipe. Do not use for actual modeling. Rather, intended
  for debugging multiprocessing; API mimics
  MultiprocessingMaster, but runs synchronously in one thread.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousSerializingWorker

class SynchronousMaster(SharedMemoryMasterBase):
  '''Controls SynchronousWorkers. Default
  Master. Communicates via SynchronousPipe.  This is what you
  want if you don't want to pay for parallelism.

  '''
  @staticmethod
  def _pipe_and_process_types():
    return SynchronousPipe, SynchronousWorker

######################################################################
# Per-process workers; interact with individual objects
######################################################################

class Safely(object):
  """Wraps "safely" around all the methods of the argument.

  """
  def __init__(self, obj): self.obj = obj

  def __getattr__(self, attrname):
    # @safely doesn't work as a decorator here; do it this way.
    return safely(safely(getattr)(self.obj, attrname))


class WorkerBase(object):

  '''The base class is WorkerBase, which manages a list of objects
  synchronously (using Safely objects to catch exceptions).

  '''
  def __init__(self, objs, pipe):
    self.objs = [Safely(o) for o in objs]
    self.pipe = pipe
    self._initialize()

  def run(self):
    done = False
    while not done:
      done = self.poll()

  def poll(self):
    cmd, args, kwargs, index = self.pipe.recv()
    if cmd == 'stop':
      return True # Done
    if hasattr(self, cmd):
      res = getattr(self, cmd)(index, *args, **kwargs)
    elif index is not None:
      res = getattr(self.objs[index], cmd)(*args, **kwargs)
    else:
      res = [getattr(o, cmd)(*args, **kwargs) for o in self.objs]
    self.pipe.send(res)
    return False # Maybe not done

  @safely
  def set_seeds(self, _index, seeds):
    # If we're in puma, set the seed; else don't.
    # The truly parallel case is handled by the subclass MultiprocessingWorker.
    did_set_global_prng = False
    for (obj, seed) in zip(self.objs, seeds):
      if hasattr(obj, "has_own_prng") and obj.has_own_prng():
        obj.set_seed(seed)
      elif not did_set_global_prng and self.should_set_global_prng():
        random.seed(seed)
        np.random.seed(seed)
        did_set_global_prng = True
    return [None for _ in self.objs]

  # Except in the true multiprocessing case (which overrides this
  # method), a Worker can just inherit the ambient PRNG from the
  # controlling Python process.
  def should_set_global_prng(self): return False

  def send_object(self, _index):
    raise VentureException("fatal", "Cannot transmit object directly if memory is not shared")

######################################################################
# Base classes defining how to send objects, and process types

class SharedMemoryWorkerBase(WorkerBase):
  '''Offers a short-cut around serialization by sending objects directly.

  Only works if the memory space is shared between worker and master,
  and we are not trying to emulate the separate-memory regime.
  Inherited by ThreadedWorker and SynchronousWorker.

  '''
  @safely
  def send_object(self, index):
    if index is not None:
      return self.objs[index].obj
    else:
      return [o.obj for o in self.objs]

class MultiprocessBase(mp.Process):
  '''
  Specifies multiprocess implementation; inherited by MultiprocessingWorker.
  '''
  def _initialize(self):
    mp.Process.__init__(self)
    self.daemon = True

class ThreadingBase(mpd.Process):
  '''
  Specifies threaded implementation; inherited by ThreadedSerializingWorker
  and ThreadedWorker.
  '''
  def _initialize(self):
    mpd.Process.__init__(self)
    self.daemon = True

class SynchronousBase(object):
  '''Specifies synchronous implementation; inherited by
  SynchronousSerializingWorker and SynchronousWorker.
  '''
  def _initialize(self):
    self.pipe.register_callback(self.poll)

  def start(self): pass

######################################################################
# Concrete process classes

# pylint: disable=too-many-ancestors
class MultiprocessingWorker(WorkerBase, MultiprocessBase):
  '''
  True parallelism via multiprocessing. Controlled by MultiprocessingMaster.
  '''

  # Each MultiprocessingWorker is (implicitly) in charge of the PRNG
  # of the process running it.
  def should_set_global_prng(self): return True

class ThreadedSerializingWorker(WorkerBase, ThreadingBase):
  '''Emulates MultiprocessingWorker by forbidding the short-cut
  around serializing the managed objects, but is implemented with
  threading. Could be useful for debugging?  Controlled by
  ThreadedSerializingMaster.

  '''
  pass

class ThreadedWorker(SharedMemoryWorkerBase, ThreadingBase):
  '''Emulates MultiprocessingWorker by running multithreaded, but
  permits the shared-memory shortcut around serialization.  Could be
  useful for debugging?  Controlled by ThreadedMaster.

  '''
  pass

class SynchronousSerializingWorker(WorkerBase, SynchronousBase):
  '''Emulates MultiprocessingWorker by forbidding the
  serialization short-cut as it would, while still running in one
  thread.  Use for debugging.  Controlled by
  SynchronousSerializingMaster.

  '''
  pass

class SynchronousWorker(SharedMemoryWorkerBase, SynchronousBase):
  '''Default. Keeps everything synchronous, and short-cuts around
  serialization. Controlled by SynchronousMaster.

  '''
  pass

######################################################################
# Code to handle exceptions in worker processes
######################################################################

class WorkerExceptionHandler(object):
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
