import subprocess,os,time
from subprocess import PIPE,STDOUT,Popen
from time import sleep,time

file_dir = os.path.dirname(os.path.realpath(__file__))
loc_para_test = file_dir + '/para_test.ipy'
loc_ip_parallel = '/'.join( file_dir.split('/')[:-2] + ['python','lib','venturemagics','ip_parallel.py'] )   

def test_ip_parallel():

    def checkOutput(cmd,time_before_kill):
        a = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        print 'para_test.ipy subprocess pid', a.pid
        start = time()
        while a.poll() == None or time()-start <= time_before_kill: #30 sec grace period
            sleep(0.25)
        if a.poll() == None:
            print 'para_test Still running, kill process'
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
    
    time_before_kill = 50
    out = checkOutput(['ipython',loc_para_test,loc_ip_parallel],time_before_kill)
    
    
    if 'assertion' in out.lower():
        assert False, 'Error running para_test.ipy in IPython'

    print 'test_parahelp on para_test.ipy on ip_parallel out and error: \n'
    print out    
   

