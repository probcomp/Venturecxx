from venture.shortcuts import make_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
import time,os,subprocess
import numpy as np
from IPython.parallel import Client
from nose.tools import with_setup

## IMPORT VERSION OF IP_PARA, TESTS
##FIXME: currently, seed based tests don't fully work for lite and so we skip them
lite = False 
mk_ripl = make_church_prime_ripl if not(lite) else make_lite_church_prime_ripl
from int_ip_parallel import *



def setup_function():
    print 'START SETUP'
    def start_engines(no_engines,sleeptime=20):
        start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
        time.sleep(sleeptime)
    try: 
        start_engines(2,sleeptime=10)
        print 'SUBPROCESS IPCLUS START SUCCESS'
    except: assert False,"subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines])"

    file_dir = os.path.dirname(os.path.realpath(__file__))
    loc_ip_parallel = '/'.join( file_dir.split('/')[:-2] + ['python','lib','venturemagics','ip_parallel.py'] )   
    # [:-2] because current file is /Venturecxx/test/venturemagics
    print 'REACHED EXEC FILE'
    #execfile(loc_ip_parallel)


def teardown_function():
    print "TEARDOWN REACHED"
    def stop_engines(): 
        stop=subprocess.Popen(['ipcluster', 'stop'])
        stop.wait()
    stop_engines()


@with_setup(setup_function,teardown_function)
def testAddRemoveSize():
    print 'IP_AddRemoveSize'
    clear_all_engines()
    no_rips = 4
    vv=MRipl(no_rips,lite=lite)

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
    print '... passed'



def testAll_IP():

    def testCopyFunction():
        print 'IP_COPY'
        clear_all_engines()
    # test for copy_ripl funtion
        myv = mk_ripl()
        myv.assume('x','(beta 1 1)'); myv.observe('(normal x 1)','5'); myv.predict('(flip)')
        assert [build_exp(di['expression']) for di in myv.list_directives() ] ==  [build_exp(di['expression']) for di in copy_ripl(myv).list_directives() ]
        print '...passed'

    def testParallelCopyFunction():
    # test for parallel use of copy_ripl_string

        cli = Client(); dv = cli[:]; dv.block=True
        dv.push(copy_ripl_dict)
        if not(lite):
            dv.execute('from venture.shortcuts import make_church_prime_ripl as mk_ripl')
        else:
            dv.execute('from venture.shortcuts import make_lite_church_prime_ripl as mk_ripl')
        dv.execute('v=mk_ripl()')
        dv.execute('v.set_seed(1)')
        dv.execute("v.assume('x','(beta 1 1)'); v.observe('(normal x 1)','5'); v.predict('(flip)')" )
        dv.execute("v2 = copy_ripl(v,seed=1)" )
        dv.execute("true_assert = [build_exp(di['expression']) for di in v.list_directives() ] ==  [build_exp(di['expression']) for di in copy_ripl(v).list_directives() ]")
        assert all(dv['true_assert'])
        print '... passed'

    ## TEST adding and removing ripls and pulling info about ripls to mripl

    def testAddRemoveSize():
        clear_all_engines();print 'IP_addremove  '
        no_rips = 4
        vv=MRipl(no_rips,lite=lite)

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
        print '... passed'

    def testCopyRipl():
        # create rips, add an assume. add some rips. get some reports
        # and see if reports are all the same. 
        clear_all_engines();print 'IP_copy  '
        no_rips = 4
        vv = MRipl(no_rips,lite=lite)
        vv.assume('x','3.')

        no_rips += 3
        vv.add_ripls(3)
        assert( vv.report(1) == ( [3.]*no_rips ) )
        no_rips -= 6
        vv.remove_ripls(6)
        ## FIXME fails because remove_ripls will preserve one ripl per engine
        #assert( vv.report(1) == ( [3.] * no_rips ) )
        print '... passed'

    def testDirectives():
        ## TEST DIRECTIVES
        clear_all_engines();print 'IP_directives  '

        v = MRipl(2,lite=lite)
        test_v = mk_ripl(); test_v.set_seed(0)
        ls_x = v.assume('x','(uniform_continuous 0 1000)')
        test_x = test_v.assume('x','(uniform_continuous 0 1000)')
        local_x = v.local_ripl.report(1)
        if not(lite): assert( np.round(test_x) in np.round(ls_x) )
        assert( np.round(local_x) in np.round(ls_x) )

        # # this fails with val = '-10.'
        v.observe('(normal x 50)','-10')
        test_v.observe('(normal x 50)','-10')
        ls_obs = v.report(2);
        test_obs = test_v.report(2)
        local_obs = v.local_ripl.report(2)
        if not(lite): assert( ( [ np.round(test_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )
        assert( ( [np.round(local_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )

        v.infer(120); test_v.infer(120)
        ls_x2 = v.report(1); test_x2 = test_v.report(1);
        local_x2 = v.local_ripl.report(1)
        if not(lite): assert( np.round(test_x2) in np.round(ls_x2) )
        assert( np.round(local_x2) in np.round(ls_x2) )
        if not(lite): assert( np.mean(test_x2) < np.mean(test_x) )
        if not(lite): assert( not( v.no_ripls>10 and np.mean(test_x2) > 50) ) # may be too tight


        ls_x3=v.predict('(normal x .1)')
        test_x3 = test_v.predict('(normal x .1)')
        local_x3 = v.local_ripl.predict('(normal x .1)')
        if not(lite): assert( np.round(test_x3) in np.round(ls_x3) )
        assert( np.round(local_x3) in np.round(ls_x3) )
        if not(lite): assert( np.mean(test_x3) < np.mean(test_x) )
        if not(lite): assert( not( v.no_ripls>10 and np.mean(test_x3) > 50) ) # may be too tight

        # test sp values
        clear_all_engines(); v=MRipl(2,lite=lite)
        v.assume('f','(lambda()(33))')
        v.assume('hof','(lambda() (lambda()(+ 1 3)) )')
        v.predict('(hof)')
        
        v.assume('h','(lambda () (flip) )')
        v.sample('(h)')
        v.observe('(h)','true')

    ## other directives
        clear_all_engines(); v=MRipl(2,lite=lite)
        test_v = mk_ripl(); test_v.set_seed(0)
        vs = [v, test_v]
        [r.assume('x','(normal 0 1)') for r in vs]

        [r.observe('(normal x .01)','1',label='obs') for r in vs]
        [r.infer(100) for r in vs]
        [r.forget('obs') for r in vs]
        [r.infer(100) for r in vs]
        pred = [r.predict('x') for r in vs]
        if not(lite): assert pred[1] in pred[0]
        if not(lite): assert v.local_ripl.predict('x') in pred[0], 'forget'

        log = [r.get_global_logscore() for r in vs]
        if not(lite): assert log[1] in log[0]
        if not(lite): v.local_ripl.get_global_logscore() in log[0], 'get_global_log'

        [r.clear() for r in vs]
        ld = [r.list_directives() for r in vs] + [v.local_ripl.list_directives() ]
        if not(lite): assert ld==[ [[],[]], [], [] ], 'clear_listdir'
        # 2 is number of ripls in v (above)

        [r.clear() for r in vs]
        prog = '[assume x 1]'
        ex = [r.execute_program(prog) for r in vs]
        if not(lite): assert ex[0][0] == ex[0][1] == ex[1]
        print '... passed'

    def testSnapshot():

        if not(lite):
            clear_all_engines();print 'IP_snap  '
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
            clear_all_engines();print 'IP_snap  '
            no_rips=2
            v=MRipl(no_rips,lite=lite)
            v.assume('x','(binomial 10 .5)',label='x')
            v.assume('y','3.',label='y')
            seeds_poisson = [15.,4.,9.,11.] #precomputed
            s=v.snapshot('x'); xs = s['values']['x']
            vals = [ xs[ripl['seed']] for ripl in s['ripls_info'] ]
            if not(lite): assert seeds_poisson == vals

            assert v.snapshot('y')['values']['y'] == ([3.]*no_rips)
            assert v.snapshot('y')['total_transitions'] == 0
            assert len(v.snapshot('y')['ripls_info']) == no_rips
            print '... passed'

    def testMulti():
        if not(lite):
            clear_all_engines();print 'IP_multi  '
            no_rips = 4; no_mrips=2;
            vs = [MRipl(no_rips,lite=lite) for i in range(no_mrips) ]

            #test mrids unique
            assert len(set([v.mrid for v in vs]) ) == len(vs)

            # test with different models
            [v.assume('x',str(i)) for v,i in zip(vs,[0,1]) ]
            assert all([v.sample('x') == ([i]*no_rips) for v,i in zip(vs,[0,1]) ] )

            # test clear
            [v.clear() for v in vs]
            assert all([v.total_transitions== 0 for v in vs])
            assert  [v.list_directives() == [ [] ] * no_rips for v in vs]

            ls = [v.predict('3') for v in vs]
            assert all( [ ls[0]==i for i in ls] )

            ls = [v.predict('(poisson 10)') for v in vs]
            assert all( [ set(ls[0])==set(i) for i in ls] ) # because seeds the same

            [v.clear() for v in vs]
            [v.assume('x','(normal 0 1)',label='x') for v in vs]
            [v.observe('(normal x .1)','2.',label='obs') for v in vs]
            [v.infer(100) for v in vs]
            ls=[v.report('x') for v in vs]
            assert all( [ set(ls[0])==set(i) for i in ls] ) # because seeds the same
            print '... passed'

        else:
            clear_all_engines();print 'IP_multi  '
            no_rips = 4; no_mrips=2;
            vs = [MRipl(no_rips,lite=lite) for i in range(no_mrips) ]

            #test mrids unique
            assert len(set([v.mrid for v in vs]) ) == len(vs)

            # test with different models
            [v.assume('x',str(i)) for v,i in zip(vs,[0,1]) ]
            assert all([v.sample('x') == ([i]*no_rips) for v,i in zip(vs,[0,1]) ] )

            # test clear
            [v.clear() for v in vs]
            assert all([v.total_transitions== 0 for v in vs])
            assert  [v.list_directives() == [ [] ] * no_rips for v in vs]

            ls = [v.predict('3') for v in vs]
            assert all( [ ls[0]==i for i in ls] )

            ls = [v.predict('(binomial 10 .5)') for v in vs]
            ##FIXME: deal with problem of seeds not being same for lite
            if not(lite): assert all( [ set(ls[0])==set(i) for i in ls] ) # because seeds the same

            [v.clear() for v in vs]
            [v.assume('x','(normal 0 1)',label='x') for v in vs]
            [v.observe('(normal x .1)','2.',label='obs') for v in vs]
            [v.infer(100) for v in vs]
            ls=[v.report('x') for v in vs]
            if not(lite): assert all( [ set(ls[0])==set(i) for i in ls] ) # because seeds the same
            print '... passed'


    def testMrMap():
        if not(lite):
            clear_all_engines();print 'IP_map  '
            no_rips = 4
            v = MRipl(no_rips,lite=lite)
            def f(ripl):
                import numpy
                ys = numpy.power([1, 2, 3, 4],2)
                return [ripl.predict(str(y)) for y in ys]
            out_dict = mr_map_nomagic(v,f)
            assert out_dict['info']['mripl'] == v.name_mrid
            assert all( np.array( out_dict['out'][0] ) == np.power([1, 2, 3, 4],2) )

            # compare using map to get poisson from all ripls, vs. using normal diretive
            v.clear()
            def g(ripl):
                mean = 10
                return ripl.predict('(poisson %i)' % mean)
            out_dict2 = mr_map_nomagic(v,g)
            assert out_dict2['info']['mripl'] == v.name_mrid

            vv=MRipl(no_rips); mean = 10
            vv_out = vv.predict('(poisson %i)' % mean)
            assert out_dict2['out'] == vv_out

            ## interaction with add_ripls
            v.clear()
            v.add_ripls(2)
            out_dict3 = mr_map_nomagic(v,g)
            # new seeds the same as old
            assert set(out_dict2['out']).issubset( set(out_dict3['out']) ) 


        else:
            clear_all_engines();print 'IP_map  '
            no_rips = 4
            v = MRipl(no_rips,lite=lite)
            def f(ripl):
                import numpy
                ys = numpy.power([1, 2, 3, 4],2)
                return [ripl.predict(str(y)) for y in ys]
            out_dict = mr_map_nomagic(v,f)
            assert out_dict['info']['mripl'] == v.name_mrid
            assert all( np.array( out_dict['out'][0] ) == np.power([1, 2, 3, 4],2) )

            # compare using map to get poisson from all ripls, vs. using normal diretive
            v.clear()
            def g(ripl):
                mean = 10
                return ripl.predict('(binomial %i 0.5)' % mean)
            out_dict2 = mr_map_nomagic(v,g)
            assert out_dict2['info']['mripl'] == v.name_mrid

            vv=MRipl(no_rips,lite=lite); mean = 10
            vv_out = vv.predict('(binomial %i 0.5)' % mean)
            assert out_dict2['out'] == vv_out

            ## interaction with add_ripls
            v.clear()
            v.add_ripls(2)
            out_dict3 = mr_map_nomagic(v,g)
            ## FIXME reinstate
            # new seeds the same as old
            if not(lite): assert set(out_dict2['out']).issubset( set(out_dict3['out']) ) 

            print '... passed'

##FIXME MrMap
    tests = [ testMrMap, testMulti, testSnapshot, testDirectives,testCopyRipl,testAddRemoveSize,testParallelCopyFunction,testCopyFunction]
    [t() for t in tests]
    print 'passed all tests for ip_parallel'
