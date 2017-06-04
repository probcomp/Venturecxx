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

import cPickle as pickle
import os
import struct
import traceback

from multiprocessing import Process
from multiprocessing import Pipe
from multiprocessing import cpu_count


def le32enc(n):
    return struct.pack('<I', n)

def le32dec(s):
    return struct.unpack('<I', s)[0]


# Not using multiprocessing.pool because it is not clear how to get it
# to share data from the parent to the child process.
def parallel_map(f, l, parallelism=None):

    ncpu = cpu_count() if parallelism is None else parallelism

    # Per-process action: grab an input from the input queue, compute,
    # toss the output in the output queue.
    def process_input(childno, inq_rd, outq_wr, retq_wr):
        while True:
            i = inq_rd.recv()
            if i is None:
                break
            x = l[i]
            try:
                ok, fx = True, f(x)
            except Exception as e:
                ok, fx = False, traceback.format_exc()
            os.write(retq_wr, le32enc(childno))
            try:
                outq_wr.send((i, ok, fx))
            except pickle.PicklingError:
                outq_wr.send((i, False, traceback.format_exc()))

    def process_output(fl, ctr, output):
        (i, ok, fx) = output
        if not ok:
            raise RuntimeError('Subprocess failed: %s' % (fx,))
        fl[i] = fx
        ctr[0] -= 1

    # Create the queues and worker processes.
    retq_rd, retq_wr = os.pipe()
    inq = [Pipe(duplex=False) for _ in xrange(ncpu)]
    outq = [Pipe(duplex=False) for _ in xrange(ncpu)]
    process = [
        Process(target=process_input, args=(j, inq[j][0], outq[j][1], retq_wr))
        for j in xrange(ncpu)
    ]

    # Prepare to bail by terminating all the worker processes.
    try:

        # Start the worker processes.
        for p in process:
            p.start()

        # Queue up the tasks one by one.  If the input queue is full,
        # process an output item to free up a worker process and try
        # again.
        n = len(l)
        fl = [None] * n
        ctr = [n]
        iterator = iter(xrange(n))
        for j, i in zip(xrange(ncpu), iterator):
            inq[j][1].send(i)
        for i in iterator:
            j = le32dec(os.read(retq_rd, 4))
            process_output(fl, ctr, outq[j][0].recv())
            inq[j][1].send(i)

        # Process all the remaining output items.
        while 0 < ctr[0]:
            j = le32dec(os.read(retq_rd, 4))
            process_output(fl, ctr, outq[j][0].recv())

        # Cancel all the worker processes.
        for _inq_rd, inq_wr in inq:
            inq_wr.send(None)

        # Wait for all the worker processes to complete.
        for p in process:
            p.join()

    except Exception as e:           # paranoia
        # Terminate all subprocesses immediately and reraise.
        for p in process:
            if p.is_alive():
                p.terminate()
        raise

    finally:
        os.close(retq_rd)
        os.close(retq_wr)
        for inq_rd, inq_wr in inq:
            inq_rd.close()
            inq_wr.close()
        for outq_rd, outq_wr in outq:
            outq_rd.close()
            outq_wr.close()

    return fl
