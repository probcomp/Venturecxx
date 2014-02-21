import subprocess,os

file_dir = os.path.dirname(os.path.realpath(__file__))
test_file = file_dir + '/para_test.ipy'

out = subprocess.check_output(['ipython',test_file])
print 'para_test output',out

if 'error' in out.lower() or 'assertion' in out.lower():
    assert False, 'Error running %s in IPython' % test_file
    stop = subprocess.Popen(['ipcluster','stop'])
    stop.wait()
else:
    print "PARA_TEST IPYTHON PASS"
