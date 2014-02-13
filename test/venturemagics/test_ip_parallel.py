from venture.shortcuts import make_church_prime_ripl
import time,os
import numpy as np

## Testing for /python/lib/ip_parallel.py

## IP_parallel uses IPython features. However, we can test
# them in normal Python by importing the relvant bits of IPython.
# This import is done in ip_parallel.py itself. This
# test script executes ip_parallel.py (rather than importing) and so
# has the IPython features (e.g. 'Client()') in its namespace.
# If future versions of ip_parallel.py or its tests use unimported
# IPython features, the tests will have to be altered.

# Note: ipcluster engines need to be running for the tests to work.




## FIXME we want to find ip_parallel without importing it
# (importing breaks it due to use of parallel)
# we currently get its path by using os.path on this very test file, but
# this is brittle and should be improved on

file_dir = os.path.dirname(os.path.realpath(__file__))
loc_ip_parallel = '/'.join( file_dir.split('/')[:-2] + ['python','lib','venturemagics','ip_parallel.py'] )   
# [:-2] because current file is /Venturecxx/test/venturemagics


execfile(loc_ip_parallel)


# Tests below all depend on finding ipcluster engines or starting them successfully
try: 
    cli=Client() # try to find existing engines
except:
    try: start_engines(2,sleeptime=30)
    except: print "test_ip_parallel: FAILED, couldn't start engines"




def testCopyFunction():
    clear_all_engines()
# test for copy_ripl funtion
    myv = make_church_prime_ripl()
    myv.assume('x','(beta 1 1)'); myv.observe('(normal x 1)','5'); myv.predict('(flip)')
    assert [build_exp(di['expression']) for di in myv.list_directives() ] ==  [build_exp(di['expression']) for di in copy_ripl(myv).list_directives() ]

def testParallelCopyFunction():
# test for parallel use of copy_ripl_string

    cli = Client(); dv = cli[:]; dv.block=True
    dv.execute(copy_ripl_string)
    dv.execute('from venture.shortcuts import make_church_prime_ripl')
    dv.execute('v=make_church_prime_ripl()')
    dv.execute('v.set_seed(1)')
    dv.execute("v.assume('x','(beta 1 1)'); v.observe('(normal x 1)','5'); v.predict('(flip)')" )
    dv.execute("v2 = copy_ripl(v,seed=1)" )
    dv.execute("true_assert = [build_exp(di['expression']) for di in v.list_directives() ] ==  [build_exp(di['expression']) for di in copy_ripl(v).list_directives() ]")
    assert all(dv['true_assert'])


## TEST adding and removing ripls and pulling info about ripls to mripl

def testAddRemoveSize():
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

def testCopyRipl():
    # create rips, add an assume. add some rips. get some reports
    # and see if reports are all the same. 
    clear_all_engines()
    no_rips = 4
    vv = MRipl(no_rips)
    vv.assume('x','3.')
    
    no_rips += 3
    vv.add_ripls(3)
    assert( vv.report(1) == ( [3.]*no_rips ) )
    no_rips -= 6
    vv.remove_ripls(6)
    ## FIXME fails because remove_ripls will preserve one ripl per engine
    #assert( vv.report(1) == ( [3.] * no_rips ) )
    

def testDirectives():
    ## TEST DIRECTIVES
    clear_all_engines()
    
    v = MRipl(2)
    test_v = make_church_prime_ripl(); test_v.set_seed(0)
    ls_x = v.assume('x','(uniform_continuous 0 1000)')
    test_x = test_v.assume('x','(uniform_continuous 0 1000)')
    local_x = v.local_ripl.report(1)
    assert( np.round(test_x) in np.round(ls_x) )
    assert( np.round(local_x) in np.round(ls_x) )

    # # this fails with val = '-10.'
    v.observe('(normal x 50)','-10')
    test_v.observe('(normal x 50)','-10')
    ls_obs = v.report(2);
    test_obs = test_v.report(2)
    local_obs = v.local_ripl.report(2)
    assert( ( [ np.round(test_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )
    assert( ( [np.round(local_obs)]*v.no_ripls ) == list(np.round(ls_obs))  )

    v.infer(120); test_v.infer(120)
    ls_x2 = v.report(1); test_x2 = test_v.report(1);
    local_x2 = v.local_ripl.report(1)
    assert( np.round(test_x2) in np.round(ls_x2) )
    assert( np.round(local_x2) in np.round(ls_x2) )
    assert( np.mean(test_x2) < np.mean(test_x) )
    assert( not( v.no_ripls>10 and np.mean(test_x2) > 50) ) # may be too tight


    ls_x3=v.predict('(normal x .1)')
    test_x3 = test_v.predict('(normal x .1)')
    local_x3 = v.local_ripl.predict('(normal x .1)')
    assert( np.round(test_x3) in np.round(ls_x3) )
    assert( np.round(local_x3) in np.round(ls_x3) )
    assert( np.mean(test_x3) < np.mean(test_x) )
    assert( not( v.no_ripls>10 and np.mean(test_x3) > 50) ) # may be too tight

## other directives
    clear_all_engines(); v=MRipl(2)
    test_v = make_church_prime_ripl(); test_v.set_seed(0)
    vs = [v, test_v]
    [r.assume('x','(normal 0 1)') for r in vs]

    [r.observe('(normal x .01)','1',label='obs') for r in vs]
    [r.infer(100) for r in vs]
    [r.forget('obs') for r in vs]
    [r.infer(100) for r in vs]
    pred = [r.predict('x') for r in vs]
    assert pred[1] in pred[0] and v.local_ripl.predict('x') in pred[0], 'forget'

    log = [r.get_global_logscore() for r in vs]
    assert log[1] in log[0] and v.local_ripl.get_global_logscore() in log[0], 'get_global_log'

    [r.clear() for r in vs]
    ld = [r.list_directives() for r in vs] + [v.local_ripl.list_directives() ]
    assert ld==[ [[],[]], [], [] ], 'clear_listdir'
    # 2 is number of ripls in v (above)

    [r.clear() for r in vs]
    prog = '[assume x 1]'
    ex = [r.execute_program(prog) for r in vs]
    assert ex[0][0] == ex[0][1] == ex[1]
    

def testSnapshot():
    clear_all_engines()
    v=MRipl(4)
    v.assume('x','(poisson 10)',label='x')
    v.assume('y','3.',label='y')
    seeds_poisson = [15.,4.,9.,11.] #precomputed
    s=v.snapshot('x'); xs = s['values']['x']
    vals = [ xs[ripl['seed']] for ripl in s['ripls_info'] ]
    assert seeds_poisson == vals
    
    assert v.snapshot('y')['values']['y'] == ([3.]*4)
    assert v.snapshot('y')['total_transitions'] == 0
    assert len(v.snapshot('y')['ripls_info']) == 4

def testMulti():
    clear_all_engines()
    no_rips = 4; no_mrips=2;
    vs = [MRipl(no_rips) for i in range(no_mrips) ]
    
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



def testMrMap():
    clear_all_engines()
    no_rips = 4
    v = MRipl(no_rips)
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
    

### Tests to add
# include NB test as well as these, try to test graphing somehow and isolate weird behavior
# (test on different browsers!)

# do tests in notebook comparing results of mag and non-mag versions

# run tests solely in Python interpreter


tests = [testMrMap, testMulti, testSnapshot, testDirectives,testCopyRipl,testAddRemoveSize,testParallelCopyFunction,testCopyFunction]


def all_ip_parallel(new_engines=False,sleeptime=30):
    if new_engines:
        stop_engines()
        start_engines(2)
        print 'sleeping %i secs' % sleeptime
        time.sleep(sleeptime)
        [t() for t in tests]
        stop_engines(); time.sleep(5)
    [t() for t in tests]
    return 'testAll complete'



