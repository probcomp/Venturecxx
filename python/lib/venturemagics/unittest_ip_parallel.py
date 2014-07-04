import time,os,subprocess
import numpy as np
import scipy.stats as stats
from IPython.parallel import Client
from nose.tools import with_setup, eq_,assert_equal,assert_almost_equal
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, get_mripl
from testconfig import config

from venture.venturemagics.ip_parallel import *
#execfile('/home/owainevans/Venturecxx/python/lib/venturemagics/ip_parallel.py')



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



def testDirectivesAssume():
    'assume,report,predict,sample,observe'
    v=get_mripl(no_ripls=4)

    # test assume,report,predict,sample
    outAssume = v.assume("x","(poisson 50)",label="x")
    outs = [v.report(1), v.report("x"), v.sample("x"), v.predict("x")]
    typed = v.report(1,type=True)
    outs.append( [ type_value["value"] for type_value in typed] )
    
    outAssume= map(int,outAssumes)
    outs = map(int,outs)
    [eq_(outAssume,out) for out in outs]

    # test observe
    v.clear()
    outAssume = v.assume("x","(normal 1 1)",label="x")
    v.observe("(normal x 1)","2",label="obs")
    [assert_almost_equal(out,2) for out in v.report("obs")]
    eq_( map(int,outAssume), map(int,v.report(1)) )
    return

def testDirectivesExecute():
    "execute_program, force"
    vs=[get_mripl(no_ripls=3) for _ in range(2)]

    prog = """
    [ASSUME x (poisson 50)]
    [OBSERVE (normal x 1) 55.]
    [PREDICT x ] """

    v[0].execute_program(prog)
    eq_( v[0].report(3), v[0].report(1) )
    
    v[1].assume('x','(poisson 50)')
    eq_( v[0].report(1), v[1].report(1) )

    v[0].force('x','10')
    eq_( v[0].report(1), 10)
    eq_( v[0].report(3), 10)

@statisticalTest
def testDirectivesInfer1():
    'infer'
    v=get_mripl(no_ripls=20)
    samples = v.assume('x','(normal 1 1)')
    v.infer(5)
    samples.extend(v.report(1))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
def testDirectivesInfer2():
    'inference program'
    v=get_mripl(no_ripls=20)
    samples = v.assume('x','(normal 1 1)')
    [v.infer(params='(mh default one 1)') for _ in range(5)]
    samples.extend(v.report(1))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
def testDirectivesForget():
    'forget'
    v=get_mripl(no_ripls=8)
    v.assume('x','(normal 1 10)')
    v.observe('(normal x .1)','1')
    v.infer(20)
    v.forget(2)
    v.infer(20)
    samples = v.report(1)
    cdf = stats.norm(loc=1, scale=10).cdf
    return reportKnownContinuous(cdf,samples,"N(1,10)")
    

def testDirectivesListDirectives():
    'list_directives'
    no_ripls=4
    v=get_mripl(no_ripls=no_ripls)
    v.assume('x','(* 2 10)')
    out = v.list_directives()
    # either list_di outputs list of list_directives
    if len(out)==no_ripls: 
        di_list = out[0]
    else:
        di_list = out   # or just outputs single list
    eq_(di_list[0]['symbol'],'x')
    eq_(di_list[0]['value'],20.)
    

    
@statisticalTest
def testSeeds():
    # seeds can be set via constructor or self.mr_set_seeds
    v=get_mripl(no_ripls=8,seeds=range(8))
    eq_(v.seeds,range(8))

    v.mr_set_seeds(range(10,18))
    eq_(v.seeds,range(10,18))

    # initial seeds are distinct and stay distinct after self.clear
    v=get_mripl(no_ripls=8) 
    samples = v.sample("(normal 1 1)")
    v.clear()
    samples.extend( v.sample("(normal 1 1)") )
    cdf = stats.norm(loc=1,scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")
    
    
def testMultiMRipls():
    
    vs=[get_mripl(no_ripls=2) for _ in range(2)]
    assert vs[0].mrid != vs[1].mrid     # distinct mripl ids

    [v.mr_set_seeds(range(2)) for v in vs]
    outs = [v.sample('(poisson 20)') for v in vs]
    eq_(outs[0],outs[1])

    outs = [v.assume('x','%i'%i) for i,v in zip(range(2),vs)]
    assert outs[0] != outs[1]
    
    cleared_v = vs[0].clear()
    vs = [cleared_v,get_mripl(no_mripls=3)] # trigger del for vs[1]
    assert vs[0].mrid != vs[1].mrid     # distinct mripl ids

def testMrMap():
        v=get_mripl(no_ripls=4)
        
        # no args, no limit (proc does import)
        def f(ripl):
            import numpy as np
            return ripl.predict(str( np.power(4,2)))
        out = v.map_proc('all',f)
        assert all( 16. == np.array(out) )

        # args,kwargs,limit
        def g(ripl,x,exponent=1):
            return ripl.predict(str( x**exponent) )
        out = v.map_proc(2, g, 4, exponent=2)
        assert len(out)==2 and all( 16. == np.array(out) )
    
        # map_proc_list no_kwargs
        def h(ripl,x): return ripl.predict(str(x))
        values = v.map_proc_list(h,[[10],[20]],only_p_args=True)
        eq_(values,[10,20])

        # map_proc_list kwargs
        def foo(ripl,x,y=1): return ripl.sample('(+ %f %f)'%(x,y))
        proc_args_list = [  [ [10],{'y':10} ],  [ [30],{} ] ]
        values = v.map_proc_list(foo,proc_args_list,only_p_args=False)
        eq_( values, [20,31])
    
        # unbalanced no_ripls
        out = v.map_proc(3,f)
        assert all( 16. == np.array(out) )
        assert len(out) == 3
        
        values = v.map_proc_list(h,[[10],[20],[30]],only_p_args=True)
        assert 10 in values and 20 in values and 30 in values
        assert len(values) >= 3

        # use interactive to access remote engine namespaces
        # use fact that ip_parallel is imported to engines
        if v.local_mode is False:
            def f(ripl):
                mripl = MRipl(2,local_mode=True)
                mripl.mr_set_seeds(range(2))
                return mripl.sample('(poisson 20)')
            pairs = v.map_proc('all',f)
            pairs = [map(int,pair) for pair in pairs]
            assert all( [pairs[0]==pair for pair in pairs] )
    



def bino_model(v):
        v.assume('x','(binomial 5 .5)') 
        [v.observe(' (poisson (+ x 1))', '1.') for i in range(10) ]
        v.infer(150)
        return v.predict('x')


def compareSpeed(no_ripls=4,infer_steps=75,backends=('puma','lite')):
    'Compare speed with different backends and local/remote mode'
    name='compareSpeed'
    print 'Start %s'%name

    bkends = backends
    l_mode = [True,False]
    params=[(b,l) for b in bkends for l in l_mode]

    m_times = []

    for (b,l) in params:
        times = []
        for reps in range(3):
            start = time.time()
            v=MRipl(no_ripls,backend=b,output='remote',local_mode=l)
            out = bino_model(v)
            assert  2 > abs(np.mean(out) - 1)

            v.assume('y','(normal 5 5)')
            [v.observe('(if (flip) (normal y 1) (normal y 5))','10.') for rep in range(6)]
            v.infer(infer_steps)
            out1 = v.sample('y')
            assert 5 > abs(np.mean(out1) - 10.)
            times.append( time.time() - start )

        m_times.append( ( (b,l), np.mean(times) ) )

    sorted_times = sorted(m_times,key=lambda pair: pair[1])
    print '\ncompareSpeed Results (sorted from fastest to slowest)\n'
    print '(backend,local_mode?), mean of 3 time.time() calls in secs)\n'
    for count,pair in enumerate(sorted_times):
        print '%i:'%count, pair[0], '   %.2f'%pair[1]
    
    remotes = [pair for pair in sorted_times if False in pair[0]]
    local = [pair for pair in sorted_times if True in pair[0]]
    for r in remotes:
        for l in local:
            if r[0][:1]==l[0][:1]:
                print '\nRemote vs. Local Ratio:'
                print 'Remote %s %.2f' %(str(r[0]),r[1])
                print 'Local %s %.2f' %(str(l[0]),l[1])
                print 'Ratio %.2f' % (r[1]/l[1])
                print '--------'
        
    return sorted_times
       
 
def testLocalMode():
    name='testLocalMode'
    print 'start ', name
    for backend in ['puma','lite']:
        vl=MRipl(0,backend=backend,no_local_ripls=2,local_mode=True)
        out1 = bino_model(vl)
        assert len(out1)==vl.no_local_ripls==2
        assert 2 > abs(np.mean(out1) - 1)

        vr=MRipl(2,backend=backend,no_local_ripls=1,local_mode=False)
        out2 = bino_model(vr)
        if backend=='puma': assert all(np.array(out1)==np.array(out2))
        assert 2 > abs(np.mean(out1) - np.mean(out2))
    print 'passed %s' % name


def testBackendSwitch():
    name='testBackendSwitch'
    print 'start ', name
    cli=1#erase_initialize_mripls()

    for backend in ['puma','lite']:
        v=MRipl(2,backend=backend)
        out1 = np.mean(bino_model(v))
        s='lite' if backend=='puma' else 'puma'
        v.switch_backend(s)
        v.infer(150)
        out2 = np.mean(v.predict('x'))
        assert 2 > abs(out1 - out2)

    # start puma, switch to lite, switch back, re-do inference
    v=MRipl(2,backend='puma')
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

        v = MRipl(2,backend=backend)
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
        v=MRipl(2,backend=backend)
        v.assume('f','(lambda()(33))')
        v.assume('hof','(lambda() (lambda()(+ 1 3)) )')
        v.predict('(hof)')

        v.assume('h','(lambda () (flip) )')
        v.sample('(h)')
        v.observe('(h)','true')

    ## other directives
        v=MRipl(2,backend=backend)
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
        v=MRipl(2,backend=b,output=o, local_mode=l)
        assert v.total_transitions == 0
        v.assume('x','(student_t 4)')
        v.observe('(normal x 1)','2.')
        v.infer(10)
        assert v.total_transitions == 10
        v.clear()
        assert v.total_transitions == 0
        v.infer(10)
        assert v.total_transitions == 10
        # FIXME, add inference programming

        # switch output
        if o=='remote':
            v.output='local'
            v.infer(10)
            assert v.total_transitions == 20

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
        v=MRipl(2,backend=b,output=o, local_mode=l)
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
        vs = [MRipl(no_rips,backend=backend) for i in range(no_mrips) ]

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
    outp = ['remote']
    l_mode = [True,False] 
    params=[(b,o,l) for b in bkends for o in outp for l in l_mode]

    for (b,o,l) in params:
  
        v=MRipl(4,no_local_ripls=4, backend=b,output=o, local_mode=l)
        
        # no args, no limit (proc does import)
        def f(ripl):
            import numpy as np
            return ripl.predict(str( np.power(4,2)))
        out = mr_map_proc(v,'all',f)
        out = v.map_proc('all',f)
        assert all( 16. == np.array(out) )

        # args,kwargs,limit
        def g(ripl,x,exponent=1):
            return ripl.predict(str( x**exponent) )
        out = mr_map_proc(v,2,g,4,exponent=2)
        out = v.map_proc(2,g,4,exponent=2)
        assert len(out)==2 and all( 16. == np.array(out) )
    
        # mr_map_array no_kwargs
        def h(ripl,x): return ripl.predict(str(x))
        values = mr_map_array(v,h,[[10],[20]],no_kwargs=True)
        values = v.map_proc_list(h,[[10],[20]],only_p_args=True)

        assert values==[10,20]

        # mr_map_array kwargs
        def foo(ripl,x,y=1): return ripl.sample('(+ %f %f)'%(x,y))
        proc_args_list = [  [ [10],{'y':10} ],  [ [30],{} ] ]
        values = mr_map_array(v,foo,proc_args_list,no_kwargs=False)
        values = v.map_proc_list(foo,proc_args_list,only_p_args=False)

        assert values==[20,31]
    
        # unbalanced no_ripls
        out = mr_map_proc(v,3,f)
        out = v.map_proc(3,f)
        assert all( 16. == np.array(out) )
        assert len(out) >= 3

        values = mr_map_array(v,h,[[10],[20],[30]],no_kwargs=True)
        values = v.map_proc_list(h,[[10],[20],[30]],only_p_args=True)

        assert 10 in values and 20 in values and 30 in values
        assert len(values) >= 3

    


def testParaUtils():
    print 'testParaUtils'
    clear_all_engines()
    v=MRipl(2,lite=lite)
    v.assume('model_name','(quote kolmogorov)')
    name1 = get_name(v)
    def store_name(ripl): return get_name(ripl)
    names = mr_map_proc(v,store_name)
    assert name1==names[0]=='kolmogorov'

    print '... passed'


        
tests1 = [testLocalMode,testDirectives,testMulti,testBackendSwitch]
tests2=[testSnapshot,testTransitionsCount,testMrMap]
#[t() for t in tests]
#print 'passed all tests for ip_parallel'










