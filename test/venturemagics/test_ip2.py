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
import unittest

from IPython.parallel.util import interactive
import subprocess,time
from IPython.parallel import Client
from nose.tools import with_setup
# print 'RUNNING TEST_IP'
# no_engines = 2

# def setup_function():
#     try: 
#         subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])
#         print 'SUBPROCESS IPCLUS START SUCCESS'
#     except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"
#     time.sleep(15)
    

# def teardown_function():
#     stop=subprocess.Popen(['ipcluster', 'stop'])
#     stop.wait()
#     print  'SUBPROCESS IPCLUS START STOP SUCCESS'

def setup_function():
    no_engines = 2
    try:
        subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
        print 'SUBPROCESS IPCLUS START SUCCESS'
        time.sleep(15)
    except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"
    
def teardown_function():
    stop=subprocess.Popen(['ipcluster', 'stop'])
    stop.wait()
    print  'SUBPROCESS IPCLUS START STOP SUCCESS'


@with_setup(setup_function,teardown_function)
def test_ip_f():
    cli = Client()
    print 'CLI IDS:',cli.ids
    dv = cli[:]
    #print dv.apply(lambda:'HELLO, IM AN ENGINE')

    from IPython.parallel.util import interactive
    f = interactive(lambda: 333)
    #dv.sync_import(os)
    # def g():
    #     import sys
    #     return sys.path()

    dv.push({'f':f})
    print dv.apply_sync(f)

    # stop=subprocess.Popen(['ipcluster', 'stop'])
    # stop.wait()
    # print  'SUBPROCESS IPCLUS START STOP SUCCESS'

