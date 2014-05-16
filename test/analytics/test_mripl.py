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
    
    outAssume= map(int,outAssume)
    [eq_(outAssume,map(int,out)) for out in outs]

    # test observe
    v.clear()
    outAssume = v.assume("x","(normal 1 1)")
    v.observe("(normal x 1)","2",label="obs")
    [assert_almost_equal(out,2) for out in v.report("obs")]
    assert_almost_equal(outAssume[0],v.report(1)[0])


def testDirectivesExecute():
    "execute_program, force"
    vs=[get_mripl(no_ripls=3) for _ in range(2)]

    prog = """
    [ASSUME x (poisson 50)]
    [OBSERVE (normal x 1) 55.]
    [PREDICT x ] """

    vs[0].execute_program(prog)
    eq_( vs[0].report(3), vs[0].report(1) )
    
    vs[1].assume('x','(poisson 50)')
    eq_( vs[0].report(1), vs[1].report(1) )

    vs[0].force('x','10')
    eq_( vs[0].report(1), [10]*3)
    eq_( vs[0].report(3), [10]*3)

@statisticalTest
def testDirectivesInfer1():
    'infer'
    v=get_mripl(no_ripls=30)
    samples = v.assume('x','(normal 1 1)')
    v.infer(5)
    samples.extend(v.report(1))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
def testDirectivesInfer2():
    'inference program'
    v=get_mripl(no_ripls=30)
    samples = v.assume('x','(normal 1 1)')
    [v.infer(params='(mh default one 1)') for _ in range(5)]
    samples.extend(v.report(1))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
def testDirectivesForget():
    'forget'
    v=get_mripl(no_ripls=30)
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
    # either list_directives outputs di_list for each ripl or just one copy
    if len(out)==no_ripls: 
        di_list = out[0]
    else:
        di_list = out   
    eq_(di_list[0]['symbol'],'x')
    eq_(di_list[0]['value'],20.)
    
    
@statisticalTest
def testSeeds():
    # seeds can be set via constructor or self.mr_set_seeds
    ## TODO skip using constructor till code is stable
    #v=get_mripl(no_ripls=8,seeds=dict(local=range(1),remote=range(8)))
    #eq_(v.seeds,range(8))
    
    v=get_mripl(no_ripls=10)
    v.mr_set_seeds(range(10))
    eq_(v.seeds,range(10))

    # initial seeds are distinct and stay distinct after self.clear
    v=get_mripl(no_ripls=20) 
    v.sample("(normal 1 1)")
    v.clear()
    samples = v.sample("(normal 1 1)")
    cdf = stats.norm(loc=1,scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")
    
    
def testMultiMRipls():
    'Create multiple mripls that share the same engine namespaces'
    vs=[get_mripl(no_ripls=2) for _ in range(2)]
    assert vs[0].mrid != vs[1].mrid     # distinct mripl ids

    [v.mr_set_seeds(range(2)) for _ in vs]
    outs = [v.sample('(poisson 20)') for v in vs]
    eq_(outs[0],outs[1])

    outs = [v.assume('x','%i'%i) for i,v in zip(range(2),vs)]
    assert outs[0] != outs[1]
    
    cleared_v = vs[0].clear()
    vs = [cleared_v,get_mripl(no_ripls=3)] # trigger del for vs[1]
    assert vs[0].mrid != vs[1].mrid     # distinct mripl ids


def testMapProc():
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

 


@statisticalTest
def testBackendSwitch():
    v=get_mripl(no_ripls=30)
    new,old = ('puma','lite') if v.backend is 'lite' else ('lite','puma')
    v.assume('x','(normal 1 1)')
    v.switch_backend(new)
    assert v.report(1)[0] > 0

    v.switch_backend(old)
    assert v.report(1)[0] > 0

    cdf = stats.normal(loc=1,scale=1).cdf
    return reportKnownContinuous(cdf,v.report(1))

def testTransitionsCount():
    v=get_mripl(no_ripls=2)
    eq_( v.total_transitions, 0)
    
    v.assume('x','(student_t 4)')
    v.observe('(normal x 1)','2.')
    v.infer(10)
    eq_( v.total_transitions, 10)
    
    v.clear()
    eq_( v.total_transitions, 0)
    v.infer(10)
    eq_( v.total_transitions, 10)
    v.infer(params={'transitions':10})
    eq_( v.total_transitions, 20)
    v.infer(params='(mh default one 1)')
    eq_( v.total_transitions, 21)



def testSnapshot():

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













