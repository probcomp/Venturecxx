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
Test Venturemagics2.py by running it on notebook, IPython terminal, and regular
Python interpreter. Calls a notebook tester (nb_tester.py), a notebook
(test_venturemagics2_nb.ipynb), and a .ipy file (test_venturemagics2_ipy.ipy).
"""
import subprocess,os

from venture.test.config import in_backend, on_inf_prim


## Testing in IPython Notebook

# Script for testing notebooks taken from 
# https://github.com/ipython/ipython/wiki/Cookbook%3a-Notebook-utilities

@in_backend('puma')
@on_inf_prim("mh")
def testMagicNotebook():
    file_dir = os.path.dirname(os.path.realpath(__file__))
    notebook_tester = file_dir + '/nb_tester.py'
    test_file =  file_dir + '/test_venturemagics_nb.ipynb'
    out=subprocess.check_output(['python',notebook_tester,test_file])
    
    if 'failure' in out.lower():
        assert False, 'Notebook tester (%s) reports failure on notebook (%s)' % (
            notebook_tester, test_file)
    


## Testing in IPython
@in_backend('puma')
@on_inf_prim("mh")
def testMagicIpython():
    #raise SkipTest("The sequel fails in Jenkins for some reason.  Issue: https://app.asana.com/0/9277419963067/10168145986333")
    file_dir = os.path.dirname(os.path.realpath(__file__))
    test_file = file_dir + '/test_venturemagics_ipy.ipy'
    out = subprocess.check_output(['ipython',test_file])
    print 'test_ipy output', out
    if 'error' in out.lower() or 'assertion' in out.lower():
        assert False, 'Error running %s in IPython' % test_file



## Test in Python (weak test because can't test IPython magics)
@in_backend('puma')
@on_inf_prim("mh")
def testMagicPython():
    from venture.venturemagics.venturemagics import ipy_ripl
    ipy_ripl.assume('x1','(flip)')
    ipy_ripl.infer(10)
    ipy_ripl.assume('x5','(beta 1 1)')
    assert True==ipy_ripl.predict('true')
    assert ipy_ripl.predict('x5')>0

