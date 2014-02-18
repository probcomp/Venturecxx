import subprocess
from IPython.parallel import Client
print 'RUNNING TEST_IP'
no_engines = 2
try: 
    subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])
    print 'SUBPROCESS IPCLUS START SUCCESS'
except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"
cli = Client()
print 'CLI IDS:',cli.ids
dv = cli[:]
print dv.apply(lambda:'HELLO, IM AN ENGINE')

stop=subprocess.Popen(['ipcluster', 'stop'])
stop.wait()
print  'SUBPROCESS IPCLUS START STOP SUCCESS'
