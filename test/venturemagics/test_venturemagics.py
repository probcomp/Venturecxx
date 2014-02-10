#!/usr/bin/env python

from nose import SkipTest

"""
Test Venturemagics2.py by running it on notebook, IPython terminal, and regular
Python interpreter. Calls a notebook tester (nb_tester.py), a notebook
(test_venturemagics2_nb.ipynb), and a .ipy file (test_venturemagics2_ipy.ipy).
"""
import subprocess



## Testing in IPython Notebook

# Script for testing notebooks taken from 
# https://github.com/ipython/ipython/wiki/Cookbook%3a-Notebook-utilities

def testMagicNotebook():
    notebook_tester = 'test/venturemagics/nb_tester.py'
    test_file =  'test/venturemagics/test_venturemagics_nb.ipynb'
    
    out=subprocess.check_output(['python',notebook_tester,test_file])
    
    if 'failure' in out.lower():
        assert False, 'Notebook tester (%s) reports failure on notebook (%s)' % (
            notebook_tester, test_file)
    
    raise SkipTest("The sequel fails in Jenkins for some reason.  Issue: https://app.asana.com/0/9277419963067/10168145986333")



## Testing in IPython
def testMagicIpython():
    test_file = 'test/venturemagics/test_venturemagics_ipy.ipy'
    out = subprocess.check_output(['ipython',test_file])
    if 'error' in out.lower() or 'assertion' in out.lower():
        assert False, 'Error running %s in IPython' % test_file



## Test in Python (weak test because can't test IPython magics)
def testMagicPython():
    from venture.venturemagics.venturemagics import *
    ipy_ripl.assume('x1','(flip)')
    ipy_ripl.infer(10)
    ipy_ripl.assume('x5','(beta 1 1)')
    assert(True==ipy_ripl.predict('true'))
    assert(ipy_ripl.predict('x5')>0)










