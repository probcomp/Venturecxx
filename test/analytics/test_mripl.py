# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import time,subprocess
import numpy as np
import scipy.stats as stats
from IPython.parallel import Client
from nose.tools import with_setup, eq_,assert_equal,assert_almost_equal
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, get_mripl, default_num_samples, default_num_transitions_per_sample, on_inf_prim

import venture.venturemagics.ip_parallel as ip_parallel


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


## TOGGLE REMOTE MODE
#LOCALMODE=True
#def get_mripl(no_ripls=2,**kwargs): return MRipl(no_ripls,local_mode=LOCALMODE)


def localRunFunctions():
    tests = []
    for k,v in globals().iteritems():
        if hasattr(v,'__call__') and k.startswith('test'):
            print k,v
            tests.append( v )
    [t() for t in tests]


@on_inf_prim("none")
def testInitSwitchLocal():
    'if no engines are running, should switch to local'
    try:
        v=ip_parallel.MRipl(2)
        if v.local_mode is True:
            eq_(v.no_local_ripls,v.no_ripls)
    except:
        print 'Exception caused by doing "try" on Client"'


@on_inf_prim("none")
def testDirectivesAssume():
    'assume,report,predict,sample,observe'
    v=get_mripl(no_ripls=4)
    print 'LOCAL MODE == ',v.local_mode

    # test assume,report,predict,sample
    outAssume = v.assume("x","(poisson 50)",label="x")
    outs = [v.report("x"), v.report("x"), v.sample("x"), v.predict("x")]
    typed = v.report("x",type=True)
    outs.append( [ type_value["value"] for type_value in typed] )

    outAssume= map(int,outAssume)
    [eq_(outAssume,map(int,out)) for out in outs]

    # test observe
    v.clear()
    outAssume = v.assume("x","(normal 1 1)",label="x")
    v.observe("(normal x 1)","2",label="obs")
    [assert_almost_equal(out,2) for out in v.report("obs")]
    assert_almost_equal(outAssume[0],v.report("x")[0])


@on_inf_prim("none")
def testDirectivesExecute():
    "execute_program, force"
    v = get_mripl(no_ripls=3)

    prog = """
    pid1 : [ASSUME x (+ 1 (* 0 (poisson 50)) )]
    pid2 : [PREDICT x ]
    pid3 : [ASSUME y (poisson 50) ]
    pid4 : [OBSERVE (normal x 1) 55.]
    """
    v.execute_program(prog)
    eq_( v.report('pid2'), v.report('pid1') )

    assert v.report('pid3') >=  0
    eq_(v.report('pid4')[0],55)

    v.force('y','10')
    eq_( v.report('pid3')[0], 10)

@statisticalTest
@on_inf_prim("mh")
def testDirectivesInfer1():
    'infer'
    v=get_mripl(no_ripls=default_num_samples())
    samples = v.assume('x','(normal 1 1)',label='pid')
    v.infer(5)
    samples.extend(v.report('pid'))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
@on_inf_prim("mh")
def testDirectivesInfer2():
    'inference program'
    v=get_mripl(no_ripls=default_num_samples())
    samples = v.assume('x','(normal 1 1)',label='pid')
    [v.infer(params='(mh default one 1)') for _ in range(5)]
    samples.extend(v.report('pid'))
    cdf = stats.norm(loc=1, scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")

@statisticalTest
@on_inf_prim("mh")
def testDirectivesForget():
    'forget'
    v=get_mripl(no_ripls=default_num_samples())
    v.assume('x','(normal 1 10)',label='pid')
    v.observe('(normal x .1)','1')
    v.infer(default_num_transitions_per_sample())
    v.forget(2)
    v.infer(default_num_transitions_per_sample())
    samples = v.report('pid')
    cdf = stats.norm(loc=1, scale=10).cdf
    return reportKnownContinuous(cdf,samples,"N(1,10)")


@on_inf_prim("none")
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
    eq_(di_list[0]['symbol']['value'],'x')
    eq_(di_list[0]['value'],20.)


@on_inf_prim("none")
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
    v=get_mripl(no_ripls=default_num_samples())
    v.sample("(normal 1 1)")
    v.clear()
    samples = v.sample("(normal 1 1)")
    cdf = stats.norm(loc=1,scale=1).cdf
    return reportKnownContinuous(cdf,samples,"N(1,1)")


@on_inf_prim("none")
def testMultiMRipls():
    'Create multiple mripls that share the same engine namespaces'
    vs=[get_mripl(no_ripls=2) for _ in range(2)]
    if vs[0].local_mode is False:
        assert vs[0].mrid != vs[1].mrid     # distinct mripl ids

    [v.mr_set_seeds(range(2)) for v in vs]
    outs = [v.sample('(poisson 20)') for v in vs]
    if vs[0].backend is 'puma':
        eq_(outs[0],outs[1])

    outs = [v.assume('x','%i'%i) for i,v in zip(range(2),vs)]
    assert outs[0] != outs[1]

    vs[0].clear()
    vs = [vs[0],get_mripl(no_ripls=3)] # trigger del for vs[1]
    if vs[0].local_mode is False:
        assert vs[0].mrid != vs[1].mrid     # distinct mripl ids


@on_inf_prim("none")
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

    # map_proc_list empty args (single engine)
    def setf(ripl,y=1): return {int(ripl.sample('333')), y}
    proc_args_list = [ [[], dict(y=10)]  ]
    values = v.map_proc_list(setf,proc_args_list,only_p_args=False)
    eq_( values, [ {333,10} ] )

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
            mripl = ip_parallel.MRipl(2,local_mode=True)
            mripl.mr_set_seeds(range(2))
            return mripl.sample('(poisson 20)')
        pairs = v.map_proc('all',f)
        pairs = [map(int,pair) for pair in pairs]
        assert all( [pairs[0]==pair for pair in pairs] )


@on_inf_prim("none")
@statisticalTest
def testBackendSwitch():
    raise SkipTest('Fails on PUMA Jenkins. Re-examine method code')
    v=get_mripl(no_ripls=default_num_samples())
    new,old = ('puma','lite') if v.backend is 'lite' else ('lite','puma')
    v.assume('x','(normal 200 .1)')
    v.switch_backend(new)
    assert v.report(1)[0] > 100

    v.switch_backend(old)
    assert v.report(1)[0] > 100

    cdf = stats.norm(loc=200,scale=.1).cdf
    return reportKnownContinuous(cdf,v.report(1))

@on_inf_prim("mh")
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
    v.infer(params='(mh default one 1)')
    eq_( v.total_transitions, 11)


@on_inf_prim("none")
def testSnapshot():
    # snapshot == sample
    v=get_mripl(no_ripls=2)
    v.assume('x','(binomial 10 .999)')
    eq_(v.sample('x'),v.snapshot('x')['values']['x'])

    # sample_pop == repeated samples TODO
    #eq_(v.snapshot('x',sample_populations=(2,4))['values']['x'],
    #    [v.report(1) for _ in range(4)])


@on_inf_prim("none")
def testMRiplUtils():
    'mk_directives_string, build_exp, directive_to_string'
    v=get_ripl()
    v.assume('x','(/ 10. 5.)') # x==2
    v.assume('f','(lambda () (* x 1))') # (f)==2
    v.observe('(normal x 1)','2')
    v.predict('(+ x 0)') # ==2
    v.predict('(f)')    # ==2
    di_string = ip_parallel.mk_directives_string(v)
    v.clear()
    v.execute_program(di_string)
    [eq_(v.report(i),2) for i in [1,3,4,5]]














