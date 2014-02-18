from venture.shortcuts import make_church_prime_ripl
import time,os,subprocess
import numpy as np
from IPython.parallel import Client
from nose.tools import with_setup

def setup_function():
    print 'START SETUP'
    def start_engines(no_engines,sleeptime=20):
        start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
        time.sleep(sleeptime)
    try: 
        start_engines(2,sleeptime=50)
        print 'SUBPROCESS IPCLUS START SUCCESS'
    except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"

    file_dir = os.path.dirname(os.path.realpath(__file__))
    loc_ip_parallel = '/'.join( file_dir.split('/')[:-2] + ['python','lib','venturemagics','ip_parallel.py'] )   
    # [:-2] because current file is /Venturecxx/test/venturemagics
    print 'REACHED EXEC FILE'
    execfile(loc_ip_parallel)


def teardown_function():
    print "TEARDOWN REACHED"
    def stop_engines(): 
        stop=subprocess.Popen(['ipcluster', 'stop'])
        stop.wait()

    stop_engines()

@with_setup(setup_function,teardown_function)
def testAddRemoveSize():
    print 'IP_PARALLEL ADDSIZE'
    clear_all_engines()
    no_rips = 4
    vv=MRipl(no_rips)

    def check_size(mr,no_rips):
        survey = mr.dview.apply(lambda mrid: len(mripls[mrid]), mr.mrid)
        pred = len(mr.predict('(+ 1 1)'))

        sizes = [mr.no_ripls, len(mr.seeds),
                 len(mr.ripls_location), sum(survey), pred]
        return sizes == ( [no_rips]*len(sizes) )

    assert(check_size(vv,no_rips))

    no_rips += 2
    vv.add_ripls(2)
    assert(check_size(vv,no_rips))

    no_rips -= 2
    vv.remove_ripls(2)
    assert(check_size(vv,no_rips))
