# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

import traceback

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import cpu_count


def parallel_map(f, l):

    ncpu = cpu_count()          # XXX urk

    # Per-process action: grab an input from the input queue, compute,
    # toss the output in the output queue.
    def process_input(inq, outq):
        while True:
            i = inq.get()
            if i is None:
                break
            x = l[i]
            try:
                fx = f(x)
                outq.put((i, True, fx))
            except Exception as e:
                outq.put((i, False, traceback.format_exc()))

    def process_output(fl, ctr, (i, ok, fx)):
        if not ok:
            raise RuntimeError('Subprocess failed: %s' % (fx,))
        fl[i] = fx
        ctr[0] -= 1

    # Create the queues and worker processes.
    inq = Queue(maxsize=ncpu)
    outq = Queue(maxsize=ncpu)
    processes = [Process(target=process_input, args=(inq, outq))
        for _ in xrange(ncpu)]

    # Prepare to bail by terminating all the worker processes.
    try:

        # Start the worker processes.
        for p in processes:
            p.start()

        # Queue up the tasks one by one.  If the input queue is full,
        # process an output item to free up a worker process and try
        # again.
        n = len(l)
        fl = [None] * n
        ctr = [n]
        for i in xrange(n):
            try:
                inq.put_nowait(i)
            except Queue.Full:
                process_output(fl, ctr, outq.get())
                inq.put(i)

        # Process all the remaining output items.
        while 0 < ctr[0]:
            process_output(fl, ctr, outq.get())

        # Cancel all the worker processes.
        for _p in processes:
            inq.put(None)

        # Wait for all the worker processes to complete.
        for p in processes:
            p.join()

    except:                     # paranoia
        # Terminate all subprocesses immediately and reraise.
        for p in processes:
            p.terminate()
        raise

    return fl
