import subprocess,os,time

file_dir = os.path.dirname(os.path.realpath(__file__))
test_file = file_dir + '/para_test.ipy'

out = subprocess.Popen(['ipython',test_file])
time.sleep(60)
print 'para_est out',out,'\n'
stop = subprocess.Popen(['ipcluster','stop'])
out.kill()
print 'para_test done'

# if 'error' in out.lower() or 'assertion' in out.lower():
#     assert False, 'Error running %s in IPython' % test_file
#     stop = subprocess.Popen(['ipcluster','stop'])
#     stop.wait()
# else:
#     print "PARA_TEST IPYTHON PASS"
