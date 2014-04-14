from venture.shortcuts import make_puma_church_prime_ripl as mk_p_ripl
from venture.shortcuts import make_lite_church_prime_ripl as mk_l_ripl
import time,os,subprocess
import numpy as np
from IPython.parallel import Client
from nose.tools import with_setup

from venture.venturemagics.ip_parallel_new import *
#execfile('ip_parallel_new.py')

def mk_ripl(backend):
    if backend=='puma': return mk_p_ripl()
    return mk_l_ripl()

def setup_function():
    print 'START SETUP'
    def start_engines(no_engines,sleeptime=20):
        start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
        time.sleep(sleeptime)
    try:
        cli=Client()
    except:
        try:
            start_engines(2,sleeptime=10)
            print 'IPCLUS START ... SUCCESS'
        except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"

def teardown_function():
    print "TEARDOWN REACHED"
    def stop_engines(): 
        stop=subprocess.Popen(['ipcluster', 'stop'])
        stop.wait()
    stop_engines()



@with_setup(setup_function,teardown_function)
def testAll_IP():
    def testBuildexp():
        pass

def bino_model(v):
        v.assume('x','(binomial 5 .5)') 
        [v.observe(' (poisson x)', '1.') for i in range(10) ]
        v.infer(150)
        return v.predict('x')


def compareSpeed():
    'Compare speed with different backends and local/remote mode'
    name='compareSpeed'
    print 'Start %s'%name

    bkends =['puma','lite']
    outp = ['remote','local']
    l_mode = [True,False]
    params=[(b,o,l) for b in bkends for o in outp for l in l_mode]

    m_times = []

    for (b,o,l) in params:
        times = []
        for reps in range(3):
            start = time.time()
            v=MRipl2(4,no_local_ripls=4,backend=b,output=o, local_mode=l)
            out = bino_model(v)
            assert  2 > abs(np.mean(out) - 1)

            v.assume('y','(normal 5 5)')
            [v.observe('(if (flip) (normal y 1) (normal y 5))','10.') for rep in range(6)]
            v.infer(100)
            out1 = v.sample('y')
            assert 5 > abs(np.mean(out1) - 10.)
            times.append( time.time() - start )

        m_times.append( ( (b,o,l), np.mean(times) ) )

    sorted_times = sorted(m_times,key=lambda pair: pair[1])
    print '(backend,output,local_mode?), mean of 3 time.time in secs)'
    for pair in sorted_times:
        print pair[0],'%.2f'%pair[1]
    
    remotes = [pair for pair in sorted_times if False in pair[0]]
    local = [pair for pair in sorted_times if True in pair[0]]
    for r in remotes:
        for l in local:
            if r[0][:2]==l[0][:2]:
                print 'Remote %s %.2f' %(str(r[0]),r[1])
                print 'Local %s %.2f' %(str(l[0]),l[1])
                print 'Ratio %.2f' % (r[1]/l[1])
                print '--------'
        
    return sorted_times
       
 
def testLocalMode():
    name='testLocalMode'
    print 'start ', name
    for backend in ['puma','lite']:
        vl=MRipl2(0,backend=backend,no_local_ripls=2,local_mode=True)
        out1 = bino_model(vl)
        assert len(out1)==vl.no_local_ripls==2
        assert 2 > abs(np.mean(out1) - 1)

        vr=MRipl2(2,backend=backend,no_local_ripls=1,local_mode=False)
        out2 = bino_model(vr)
        if backend=='puma': assert all(np.array(out1)==np.array(out2))
        assert 2 > abs(np.mean(out1) - np.mean(out2))
    print 'passed %s' % name


def testBackendSwitch():
    name='testBackendSwitch'
    print 'start ', name
    cli=1#erase_initialize_mripls()

    for backend in ['puma','lite']:
        v=MRipl2(2,backend=backend,client=cli)
        out1 = np.mean(bino_model(v))
        s='lite' if backend=='puma' else 'puma'
        v.switch_backend(s)
        v.infer(150)
        out2 = np.mean(v.predict('x'))
        assert 2 > abs(out1 - out2)

    # start puma, switch to lite, switch back, re-do inference
    v=MRipl2(2,backend='puma',client=cli)
    out1 = np.mean(bino_model(v))
    assert 2 > abs(out1 - 1.)
    v.switch_backend('lite')
    v.infer(150)
    out2 = np.mean(v.predict('x'))
    assert 2 > abs(out1 - out2)
    v.switch_backend('puma')
    v.infer(150)
    out3 = np.mean(v.predict('x'))
    assert 2 > abs(out1 - out3) # not same, because seeds not reset

    print 'passed %s' % name


def testDirectives():
    name='testDirectives'
    print 'start ', name

    for backend in ['puma','lite']:
        if backend=='lite':
            lite=1
        else:
            lite=0

        v = MRipl2(2,backend=backend)
        test_v = mk_ripl(backend); test_v.set_seed(0)
        ls_x = v.assume('x','(uniform_continuous 0 1000)')
        test_x = test_v.assume('x','(uniform_continuous 0 1000)')
        local_x = v.local_ripls[0].report(1)
        if not(lite): assert( np.round(test_x) in np.round(ls_x) )
        assert( np.round(local_x) in np.round(ls_x) )

        # # this fails with val = '-10.'
        v.observe('(normal x 50)','-10')
        test_v.observe('(normal x 50)','-10')
        ls_obs = v.report(2);
        test_obs = test_v.report(2)
        local_obs = v.local_ripls[0].report(2)
        if not(lite): assert( ( [ np.round(test_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )
        assert( ( [np.round(local_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )

        v.infer(120); test_v.infer(120)
        ls_x2 = v.report(1); test_x2 = test_v.report(1);
        local_x2 = v.local_ripls[0].report(1)
        if not(lite): assert( np.round(test_x2) in np.round(ls_x2) )
        assert( np.round(local_x2) in np.round(ls_x2) )
        if not(lite): assert( np.mean(test_x2) < np.mean(test_x) )
        if not(lite): assert( not( v.no_ripls>10 and np.mean(test_x2) > 50) ) # may be too tight
        ls_x3=v.predict('(normal x .1)')
        test_x3 = test_v.predict('(normal x .1)')
        local_x3 = v.local_ripls[0].predict('(normal x .1)')
        if not(lite): assert( np.round(test_x3) in np.round(ls_x3) )
        assert( np.round(local_x3) in np.round(ls_x3) )
        if not(lite): assert( np.mean(test_x3) < np.mean(test_x) )
        if not(lite): assert( not( v.no_ripls>10 and np.mean(test_x3) > 50) ) # may be too tight

        # test sp values
        v=MRipl2(2,backend=backend)
        v.assume('f','(lambda()(33))')
        v.assume('hof','(lambda() (lambda()(+ 1 3)) )')
        v.predict('(hof)')

        v.assume('h','(lambda () (flip) )')
        v.sample('(h)')
        v.observe('(h)','true')

    ## other directives
        v=MRipl2(2,backend=backend)
        test_v = mk_ripl(backend); test_v.set_seed(0)
        vs = [v, test_v]
        [r.assume('x','(normal 0 1)') for r in vs]

        [r.observe('(normal x .01)','1',label='obs') for r in vs]
        [r.infer(100) for r in vs]
        [r.forget('obs') for r in vs]
        [r.infer(100) for r in vs]
        pred = [r.predict('x') for r in vs]
        if not(lite): assert pred[1] in pred[0]
        if not(lite): assert v.local_ripls[0].predict('x') in pred[0], 'forget'

        log = [r.get_global_logscore() for r in vs]
        if not(lite): assert log[1] in log[0]
        if not(lite): v.local_ripls[0].get_global_logscore() in log[0], 'get_global_log'

        [r.clear() for r in vs]
        prog = '[assume x 1]'
        ex = [r.execute_program(prog) for r in vs]
        if not(lite): assert ex[0][0] == ex[0][1] == ex[1]

        print 'passed %s' % name




def testTransitionsCount():
    name='testTransitionsCount'
    print 'Start %s'%name

    # sample populations
    bkends =['puma','lite']
    outp = ['remote','local']
    l_mode = [True,False]
    params=[(b,o,l) for b in bkends for o in outp for l in l_mode]

    for (b,o,l) in params:
        # basic test
        v=MRipl2(2,backend=b,output=o, local_mode=l)
        assert v.total_transitions == 0
        v.assume('x','(student_t 4)')
        v.observe('(normal x 1)','2.')
        v.infer(10)
        assert v.total_transitions == 10
        v.clear()
        assert v.total_transitions == 0
        v.infer(10)
        assert v.total_transitions == 10
        v.infer(params={'transitions':10})
        assert v.total_transitions == 20
        # FIXME, add inference programming

        # switch output
        if o=='remote':
            v.output='local'
            v.infer(10)
            assert v.total_transitions == 30

    print 'Passed %s' %name




def testSnapshot():
    name='testSnapshot'
    print 'Start %s'%name

    bkends =['puma','lite']
    outp = ['remote','local']
    l_mode = [False] # not all of snapshot works in local_mode
    params=[(b,o,l) for b in bkends for o in outp for l in l_mode]

    for (b,o,l) in params:
        # snapshot == sample
        v=MRipl2(2,backend=b,output=o, local_mode=l)
        v.assume('x','(binomial 10 .999)')
        out1 = v.sample('x')
        out2 = v.snapshot('x')['values']['x']
        assert out2 == out1

        # sample_pop == repeated samples
        exp = '(normal x .001)'
        out3 = v.snapshot(exp,sample_populations=(2,30))
        out3 = out3['values'][exp]
        out4 = [v.sample(exp) for rep in range(30)]
        assert .2 > abs(np.mean(out3) - np.mean(out4))
        assert .1 > abs(np.std(out3) - np.std(out4))

        # repeat == repeated samples flattened
        out5 = v.snapshot(exp,repeat=30)['values'][exp]
        assert .2 > abs(np.mean(out5) - np.mean(out3))

        # logscore
        v.infer(10)
        log1 = v.get_global_logscore()
        log2 = v.snapshot(logscore=1)['values']['global_logscore']
        assert all(.01 > np.abs(np.array(log1)-np.array(log2)))


    print 'Passed %s' % name


def testMulti():
    name='testMulti'
    print 'start ', name
    #cli=erase_initialize_mripls()
    cli=1

    no_rips = 4; no_mrips=2;
    for backend in ['puma','lite']:
        vs = [MRipl2(no_rips,backend=backend) for i in range(no_mrips) ]

        #test mrids unique
        assert len(set([v.mrid for v in vs]) ) == len(vs)

        # test with different models
        [v.assume('x',str(i)) for v,i in zip(vs,[0,1]) ]
        assert all([v.sample('x') == ([i]*no_rips) for v,i in zip(vs,[0,1]) ] )

        # test clear
        [v.clear() for v in vs]
        assert all([v.total_transitions== 0 for v in vs])
        assert  [v.list_directives() == [ ]  for v in vs]

        # test inference gives same results for mripls with same seeds
        [v.clear() for v in vs]
        [v.assume('x','(normal 0 1)',label='x') for v in vs]
        [v.observe('(normal x .1)','2.',label='obs') for v in vs]
        [v.infer(100) for v in vs]
        ls=[v.report('x') for v in vs]
        if backend=='puma':
            assert all( [ set(ls[0])==set(i) for i in ls] ) # because seeds the same
        print 'passed %s' % name


def testMrMap():
    name='testMrMap'
    print 'start ', name

    bkends =['puma','lite']
    outp = ['remote','local']
    l_mode = [True,False] # not al local_mode
    params=[(b,o,l) for b in bkends for o in outp for l in l_mode]

    for (b,o,l) in params:
  
        v=MRipl2(4,no_local_ripls=4,backend=b,output=o, local_mode=l)
        
        # no args, no limit (proc does import)
        def f(ripl):
            import numpy as np
            return ripl.predict(str( np.power(4,2)))
        out_apply = mr_map_proc(v,'all',f)
        assert all( 16. == np.array(out_apply) )

        # args,kwargs,limit
        def g(ripl,x,exponent=1):
            return ripl.predict(str( x**exponent) )
        out_apply = mr_map_proc(v,2,g,4,exponent=2)
        assert len(out_apply)==2 and all( 16. == np.array(out_apply) )
    
        print name, 'passed'


def testParaUtils():
    print 'testParaUtils'
    clear_all_engines()
    v=MRipl(2,lite=lite)
    v.assume('model_name','(quote kolmogorov)')
    name1 = get_name(v)
    def store_name(ripl): return get_name(ripl)
    names = mr_map_proc(v,store_name)['out']
    assert name1==names[0]=='kolmogorov'

    print '... passed'


        
    #tests = [ testParaUtils, testMrMap, testMulti, testSnapshot, testDirectives, testContinuous, testCopyRipl,testAddRemoveSize,testParallelCopyFunction,testCopyFunction]
    #erase_initialize_mripls()
tests = [testDirectives,testSnapshot,testMrMap,testMulti,testBackendSwitch]
tests=[testSnapshot,testTransitionsCount,testMrMap]
#[t() for t in tests]
#print 'passed all tests for ip_parallel'










