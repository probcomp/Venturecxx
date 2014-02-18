import subprocess

no_engines = 2
try: subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])
except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"
stop=subprocess.Popen(['ipcluster', 'stop'])
stop.wait()
