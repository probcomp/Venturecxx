import subprocess

print 'RUNNING TEST_IP'
no_engines = 2
try: 
    subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])
    print 'SUBPROCESS IPCLUS START SUCCESS'
except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"
stop=subprocess.Popen(['ipcluster', 'stop'])
stop.wait()
print  'SUBPROCESS IPCLUS START STOP SUCCESS'
