import subprocess,os,time
from subprocess import PIPE,STDOUT,Popen
from time import sleep,time

##
# test_parahelp.py is a python script that can be called by nose. it calls para_test.ipy which is an ipython script that actually contains the tests of ip_parallel.py (which is a set of ipython parallel tools and cell magics for ipython). the goal is to run para_test.ipy on an ipython instance by opening a process using subprocess (from test_parahelp.py). this ipython instance, in turn, will run subprocess to start an ipcluster (so we have grandchildren of original process). we need to be sure to kill all children of the parent process before exiting. we do this via a time_out, set with variable "time_before_kill".we run the .ipy subprocess. we wait until it exits or until time limit. if it\'s still running then we kill it, which should also kill its children and so close the ipcluster (need to check this). if it\'s not running we just kill the cluster.


file_dir = os.path.dirname(os.path.realpath(__file__))
loc_para_test = file_dir + '/para_test.ipy'
loc_ip_parallel = '/'.join( file_dir.split('/')[:-2] + ['python','lib','venturemagics','ip_parallel.py'] ) 

# NOTE: may need to be increased as tests are added to para_test.ipy
time_before_kill = 20  

def test_ip_parallel():

    def checkOutput(cmd,time_before_kill):
        a = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        print 'para_test.ipy subprocess pid', a.pid
        start = time()
        while a.poll() == None or time()-start <= time_before_kill: #30 sec grace period
            sleep(0.25)
        if a.poll() == None:
            print 'para_test Still running, kill process'
            try: stop = subprocess.Popen(['ipcluster','stop'])
            except: print 'ipcluster stop failed'

            a.kill()
        else:
            print 'para_test exit code:',a.poll(), '\n killing engines \n' 
            try: stop = subprocess.Popen(['ipcluster','stop'])
            except: print 'ipcluster stop failed'
            print 'killing process'
            #a.kill()
        output = a.stdout.read()
        a.stdout.close()
        a.stdin.close()
        return output

    #para_test_out = subprocess.Popen(['ipython',loc_para_test,loc_ip_parallel],
     #                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # (output, error) = para_test_out.stdout
    # if error: print "para_test error:", error
    # print "para_test output:", output
    
    
    
    out = checkOutput(['ipython',loc_para_test,loc_ip_parallel],time_before_kill)
    
    
    if 'assertion' in out.lower():
        assert False, 'Error onpara_test.ipy. Try changing variable time_before_kill in test_parahelp.ipy'
        print 'test_parahelp on para_test.ipy on ip_parallel out and error: \n'
        print out

    
    print 'test_parahelp ... PASSED'
   

