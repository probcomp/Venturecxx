#!/usr/bin/env python

# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

"""
simple example script for running notebooks and reporting exceptions.

Usage: `checkipnb.py foo.ipynb [bar.ipynb [...]]`

Each cell is submitted to the kernel, and checked for errors.

[cloned by owain@mit https://github.com/ipython/ipython/wiki/Cookbook%3a-Notebook-utilities]
"""

import os,sys,time

from Queue import Empty

try:
    from IPython.kernel import KernelManager
except ImportError:
    from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager

from IPython.nbformat.current import reads, NotebookNode

def run_notebook(nb):
    km = KernelManager()
    km.start_kernel(stderr=open(os.devnull, 'w'))
    try:
        kc = km.client()
    except AttributeError:
        # 0.13
        kc = km
    kc.start_channels()
    shell = kc
    # simple ping:
    shell.execute("pass")
    shell.get_shell_msg()
    
    cells = 0
    failures = 0
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type != 'code':
                continue
            shell.execute(cell.input)
            # wait for finish, maximum 20s
            reply = shell.get_shell_msg(timeout=20)['content']
            if reply['status'] == 'error':
                failures += 1
                print "\nFAILURE:"
                print cell.input
                print '-----'
                print "raised:"
                print '\n'.join(reply['traceback'])
            cells += 1
            sys.stdout.write('.')

    print
    print "ran notebook %s" % nb.metadata.name
    print "    ran %3i cells" % cells
    if failures:
        print "    %3i cells raised exceptions" % failures
    kc.stop_channels()
    km.shutdown_kernel()
    del km

if __name__ == '__main__':
    for ipynb in sys.argv[1:]:
        print "running %s" % ipynb
        with open(ipynb) as f:
            nb = reads(f.read(), 'json')
        run_notebook(nb)



