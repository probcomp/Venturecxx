from venture.shortcuts import make_puma_church_prime_ripl as mk_p_ripl
from venture.shortcuts import make_lite_church_prime_ripl as mk_l_ripl
import time,os,subprocess
import numpy as np
from IPython.parallel import Client
from nose.tools import with_setup

from venture.venturemagics.ip_parallel import *
execfile('ip_parallel.py')

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
            v.assume('x','(binomial 20 .5)') 
            [v.observe(' (poisson x)', '7.') for i in range(20) ]
            v.infer(300)
            return v.predict('x')

    def testLocalMode():
        name='testLocalMode'
        print 'start ', name
        for backend in ['puma','lite']:
            vl=MRipl2(0,backend=backend,no_local_ripls=2,local_mode=True)
            out1 = bino_model(vl)
            assert len(out1)==vl.no_local_ripls==2
            assert 2 > abs(np.mean(out1) - 7)

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
            v.infer(300)
            out2 = np.mean(v.predict('x'))
            assert 2 > abs(out1 - out2)
            
        # start puma, switch to lite, switch back, re-do inference
        v=MRipl2(2,backend='puma',client=cli)
        out1 = np.mean(bino_model(v))
        assert 2 > abs(out1 - 7.)
        v.switch_backend('lite')
        v.infer(300)
        out2 = np.mean(v.predict('x'))
        assert 2 > abs(out1 - out2)
        v.switch_backend('puma')
        v.infer(300)
        out3 = np.mean(v.predict('x'))
        assert round(out1)==round(out3)

        print 'passed %s' % name


    def testDirectives():
        name='testDirectives'
        print 'start ', name
        #        cli=erase_initialize_mripls()
        cli=1

        for backend in ['puma','lite']:
            if backend=='lite':
                lite=1
            else:
                lite=0

            v = MRipl2(2,backend=backend,client=cli)
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
            v=MRipl2(2,backend=backend,client=cli)
            v.assume('f','(lambda()(33))')
            v.assume('hof','(lambda() (lambda()(+ 1 3)) )')
            v.predict('(hof)')

            v.assume('h','(lambda () (flip) )')
            v.sample('(h)')
            v.observe('(h)','true')

        ## other directives
            v=MRipl2(2,backend=backend,client=cli)
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

            333; print 'passed %s' % name


    def testContinuous():
        clear_all_engines();print 'IP_continuous  '

        v = MRipl(2,lite=lite)
        test_v = mk_ripl(); test_v.set_seed(0)

        for r in [v, test_v]:
            r.clear()
            r.assume('x', '(uniform_continuous 0 1000)')
        pred1 = v.predict('x') + [test_v.predict('x')]

        for r in [v, test_v]:
            r.start_continuous_inference()
        time.sleep(1.0)
        pred2 = v.predict('x') + [test_v.predict('x')]
        assert pred1[0] != pred2[0] and pred1[1] != pred2[1], 'continuous_infer'

        for r in [v, test_v]:
            r.observe('(normal x 10)', '-10')
        time.sleep(1.0)
        pred3 = v.predict('x') + [test_v.predict('x')]
        assert pred3[0] < pred2[0] and pred3[1] < pred2[1], 'continuous_observation'

        status = v.continuous_inference_status() + [test_v.continuous_inference_status()]
        assert all(s['running'] for s in status), 'continuous_status'

        for r in [v, test_v]:
            r.stop_continuous_inference()
        status = v.continuous_inference_status() + [test_v.continuous_inference_status()]
        assert all(not s['running'] for s in status), 'continuous_stop'

        print '... passed'



    def testSnapshot():
        print 'IP_snap  '
        def model():
            clear_all_engines()
            v=MRipl(2,lite=lite)
            v.assume('p','(beta 1 1)')
            [v.observe('(flip p)','true') for i in range(4)]
            return v
        v=model()
        log1 = v.get_global_logscore()  # expectation log(.5)
        snap1 = v.snapshot(did_labels_list=[],
                   plot=False,scatter=False,logscore=True)
        snap2 = v.snapshot(did_labels_list=[1],
                   plot=False,scatter=False,logscore=True)
        log2 = snap1['values']['global_logscore']
        log3 = snap2['values']['global_logscore']
        assert all(np.round(log1) == np.round(log2))
        assert all(np.round(log1) == np.round(log3))

        v.infer(30)
        log4 = v.get_global_logscore()
        snap3 = v.snapshot(did_labels_list=[],
                   plot=False,scatter=False,logscore=True)
        log5 = snap3['values']['global_logscore']
        assert all(np.round(log4) == np.round(log5))

        # now compare probes
        v=model()
        p_log=v.probes(logscore=True,no_transitions=30,no_probes=2)['series']
        assert all(np.round(log1)==np.round(p_log[0]))
        assert all(np.round(log4)==np.round(p_log[1]))
        
        clear_all_engines()
        

        if not(no_poisson):
            
            v=MRipl(4,lite=lite)
            v.assume('x','(poisson 10)',label='x')
            v.assume('y','3.',label='y')
            seeds_poisson = [15.,4.,9.,11.] #precomputed
            s=v.snapshot('x'); xs = s['values']['x']
            vals = [ xs[ripl['seed']] for ripl in s['ripls_info'] ]
            assert seeds_poisson == vals

            assert v.snapshot('y')['values']['y'] == ([3.]*4)
            assert v.snapshot('y')['total_transitions'] == 0
            assert len(v.snapshot('y')['ripls_info']) == 4
            print '...passed'
        else: 
            clear_all_engines()
            no_rips=2
            v=MRipl(no_rips,lite=lite)
            v.assume('x','(binomial 10 .5)',label='x')
            v.assume('y','3.',label='y')
            seeds_poisson = [15.,4.,9.,11.] #precomputed
            s=v.snapshot('x'); xs = s['values']['x']
            vals = [ xs[ripl['seed']] for ripl in s['ripls_info'] ]
            if not(no_poisson): assert seeds_poisson == vals

            assert v.snapshot('y')['values']['y'] == ([3.]*no_rips)
            assert v.snapshot('y')['total_transitions'] == 0
            assert len(v.snapshot('y')['ripls_info']) == no_rips
            clear_all_engines()
            print '... passed'


    def testMulti():
        name='testMulti'
        print 'start ', name
        #cli=erase_initialize_mripls()
        cli=1
        
        no_rips = 4; no_mrips=2;
        for backend in ['puma','lite']:
            vs = [MRipl2(no_rips,backend=backend,client=cli) for i in range(no_mrips) ]

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
            333; print 'passed %s' % name

        
    def testMrApplyProc():
        name='testMrApplyProc'
        print 'start ', name
        #cli=erase_initialize_mripls()
        cli=1
        no_rips = 4
        for backend in ['puma','lite']:
            v = MRipl2(no_rips,backend=backend,client=cli)
            def f(ripl):
                import numpy
                ys = numpy.power([1, 2, 3, 4],2)
                return [ripl.predict(str(y)) for y in ys]
            out_apply = mr_apply_proc(v,'all',f)
            assert all( np.array( out_apply[0] ) == np.power([1, 2, 3, 4],2) )

            # compare using map to get poisson from all ripls, vs. using normal directive
            v.clear()
            def g(ripl):
                mean = 10
                return ripl.predict('(poisson %i)' % mean)
            out_apply2 = mr_apply_proc(v,'all',g)

            vv=MRipl2(no_rips,backend=backend,client=cli); mean = 10
            vv_out = vv.predict('(poisson %i)' % mean)
            assert out_apply2 == vv_out
            
            print '... passed'

    
    def testParaUtils():
        print 'testParaUtils'
        clear_all_engines()
        v=MRipl(2,lite=lite)
        v.assume('model_name','(quote kolmogorov)')
        name1 = get_name(v)
        def store_name(ripl): return get_name(ripl)
        names = mr_map_f(v,store_name)['out']
        assert name1==names[0]=='kolmogorov'
        
        print '... passed'
       # test for mr_plot_cond: load a model, run mr_plot_cond
       # output should be a set of xys for each ripl we get output from
       # we can then compare that output to a local ripl, should be similar
        
        
    #tests = [ testParaUtils, testMrMap, testMulti, testSnapshot, testDirectives, testContinuous, testCopyRipl,testAddRemoveSize,testParallelCopyFunction,testCopyFunction]
    #erase_initialize_mripls()
    tests = [testDirectives,testMrApplyProc,testMulti,testBackendSwitch]
    tests=[         testLocalMode]
    [t() for t in tests]
    print 'passed all tests for ip_parallel'
