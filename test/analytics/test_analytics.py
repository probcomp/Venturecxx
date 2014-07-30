import numpy as np
import scipy.stats as stats
from itertools import product
import math

from nose import SkipTest
from nose.tools import eq_, assert_almost_equal

from venture.venturemagics.ip_parallel import MRipl
from venture.unit import *
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl,get_mripl,ignore_inference_quality,default_num_samples,gen_in_backend, gen_on_inf_prim
import venture.value.dicts as v


# TODO get rid of some tests, simplify others, make tests faster to run


## Functions used by tests
def betaModel(ripl):
    assumes=[('p','(beta 1.0 1.0)')]
    observes=[('(flip p)',v.boolean(True)) for _ in range(2)]
    queryExps =  ['(add (bernoulli p) (bernoulli p))'] # exps in python form
    for sym,exp in assumes:
        ripl.assume(sym,exp)
    for exp,literal in observes:
        ripl.observe(exp,literal)
    return ripl,assumes,observes,queryExps

def normalModel(ripl):
    assumes = [ ('x','(normal 0 100)') ]
    observes = [ ('(normal x 100)',v.number(0)) ]
    queryExps = ('(* x 2)',)
    for sym,exp in assumes:
        ripl.assume(sym,exp)
    for exp,literal in observes:
        ripl.observe(exp,literal)
    xPriorCdf = stats.norm(0,100).cdf
    return ripl,assumes,observes,queryExps,xPriorCdf

def snapshot_t(history,name,t):
    return [series.values[t] for series in history.nameToSeries[name]]

def nameToFirstValues(history,name): return history.nameToSeries[name][0].values



## Tests
def _testLoadModel(riplThunk):
    'RiplThunk could be ripl or mripl'
    v=riplThunk()
    vBackend = v.backend if isinstance(v,MRipl) else v.backend()

    v,assumes,observes,queryExps = betaModel(v)
    model = Analytics(v,queryExps=queryExps)

    def attributesMatch():
        eq_( model.backend,vBackend )
        eq_( model.assumes,assumes )
        eq_( model.observes,observes )
        eq_( model.queryExps,queryExps )
    attributesMatch() # assumes extracted from ripl_mripl

    v.clear()   # now assumes given as kwarg
    model = Analytics(v,assumes=assumes,observes=observes,queryExps=queryExps)
    attributesMatch()

def _testHistory(riplThunk):
    v=riplThunk()
    v,assumes,observes,queryExps = betaModel(v)
    samples = 5
    model = Analytics(v,queryExps=queryExps)
    history,_ = model.runFromConditional(samples,runs=1)
    eq_(history.data,observes)
    assert all( [sym in history.nameToSeries for sym,_ in assumes] )
    assert all( [exp in history.nameToSeries for exp in queryExps] )
    averageP = np.mean( history.nameToSeries['p'][0].values )
    assert_almost_equal(averageP,history.averageValue('p'))

@gen_on_inf_prim("none")
def testLoadModel():
    for riplThunk in [get_ripl, lambda:get_mripl(no_ripls=3)]:
        yield _testLoadModel, riplThunk

def testModelHistory():
    for riplThunk in [get_ripl, lambda:get_mripl(no_ripls=3)]:
        yield _testHistory, riplThunk


def _testRuns(riplThunk):
    v,_,_,queryExps,_ = normalModel( riplThunk() )
    samples = default_num_samples()
    no_runs = 4
    model = Analytics(v,queryExps=queryExps)

    history,_ = model.runFromConditional(samples,runs=no_runs)
    eq_( len(history.nameToSeries['x']), no_runs)

    for exp in ('x', queryExps[0]):
        arValues = np.array([s.values for s in history.nameToSeries[exp]])
        if not ignore_inference_quality():
            assert all(np.var(arValues,axis=0) > .0001) # var across runs time t
            assert all(np.var(arValues,axis=1) > .000001) # var within runs

def testRuns():
    riplThunks = get_ripl, lambda:get_mripl(no_ripls=4)
    for riplThunk in riplThunks:
        yield _testRuns, riplThunk


@statisticalTest
def _testInfer(riplThunk,conditional_prior,inferProg):
    v,_,_,_= betaModel( riplThunk() )
    if ignore_inference_quality():
        samples = default_num_samples()
        runs = 1
    else:
        samples = int(math.sqrt(default_num_samples()))
        runs = int(math.sqrt(default_num_samples()))
    model = Analytics(v)
    infer_kwargs = dict(runs=runs,infer=inferProg,simpleInfer=True)

    if conditional_prior == 'conditional':
        history,_ = model.runFromConditional(samples,**infer_kwargs)
        cdf = stats.beta(3,1).cdf
    else:
        history,_ = model.runConditionedFromPrior(samples,**infer_kwargs)
        dataValues = [typeVal['value'] for _,typeVal in history.data]
        noHeads = sum(dataValues)
        noTails = len(dataValues) - noHeads
        cdf = stats.beta(1+noHeads,1+noTails).cdf
        # will include gtruth (but it won't affect test)

    return reportKnownContinuous(cdf,snapshot_t(history,'p',-1))


def testRunFromConditionalInfer():
    riplThunks = get_ripl, lambda: get_mripl(no_ripls=2)
    cond_prior = 'conditional', 'prior'
    k1 = '(mh default one 1)'
    infProgs =  k1,

    for riplThunk,cond_prior,infProg in product(riplThunks,cond_prior,infProgs):
        yield _testInfer, riplThunk, cond_prior, infProg



@statisticalTest
def _testSampleFromJoint(riplThunk,useMRipl):
    if riplThunk.func_name in 'get_ripl' or useMRipl is False:
        raise SkipTest('Bug with seeds for ripls')
    v,_,_,queryExps,xPriorCdf = normalModel( riplThunk() )
    samples = default_num_samples()
    model = Analytics(v,queryExps=queryExps)
    history = model.sampleFromJoint(samples, useMRipl=useMRipl)
    xSamples = nameToFirstValues(history,'x')
    return reportKnownContinuous(xPriorCdf,xSamples)

@gen_on_inf_prim("none")
def testSampleFromJoint():
    riplThunks = get_ripl, lambda: get_mripl(no_ripls=3)
    useMRiplValues = (True,False)
    params = product(riplThunks, useMRiplValues)
    for riplThunk,useMRipl in params:
        yield _testSampleFromJoint, riplThunk, useMRipl


@statisticalTest
def _testRunFromJoint1(riplThunk,inferProg):
    if riplThunk.func_name in 'get_ripl':
        raise SkipTest('Same bug as samplefromjoint with identical ripl seeds')
    v,_,_,queryExps,xPriorCdf = normalModel( riplThunk() )
    model = Analytics(v,queryExps=queryExps)
    # variation across runs
    history = model.runFromJoint(1, runs=default_num_samples(), infer=inferProg)
    return reportKnownContinuous(xPriorCdf,snapshot_t(history,'x',0))

@statisticalTest
def _testRunFromJoint2(riplThunk,inferProg):
    v,_,_,queryExps,xPriorCdf = normalModel( riplThunk() )
    model = Analytics(v,queryExps=queryExps)
    if ignore_inference_quality():
        step_size = 1
    else:
        step_size = 20
    samples = default_num_samples()
    chain_len = step_size * samples

    # variation over single runs
    history = model.runFromJoint(chain_len, runs=1, infer=inferProg)
    XSamples = np.array(nameToFirstValues(history,'x'))
    thinXSamples = XSamples[np.arange(0,chain_len,step_size)]

    return reportKnownContinuous(xPriorCdf,thinXSamples)


def testRunFromJoint():
    tests = (_testRunFromJoint1, _testRunFromJoint2)
    riplThunks = (get_ripl, lambda: get_mripl(no_ripls=4))
    infProgs = ( None, '(mh default one 5)')

    params = product(tests,riplThunks,infProgs)

    for test,riplThunk,infProg in params:
        yield test, riplThunk, infProg


@statisticalTest
def _testCompareSampleDicts(sameDistribution):
    if sameDistribution:
        dicts = [ dict(x=np.random.normal(0,1,40)) for _ in range(2) ]
    else:
        dicts = [ dict(x=np.random.normal(0,i,40)) for i in range(1,3) ]
    cReport = compareSampleDicts(dicts,('',''),plot=False)
    assert hasattr(cReport,'reportString')
    assert hasattr(cReport,'labels')
    return cReport.statsDict['x']['KSSameContinuous'] #test result object

@gen_in_backend("none")
def testCompareSampleDicts():
    sameDistribution = True,False
    for sameDistributionValue in sameDistribution:
        yield _testCompareSampleDicts,sameDistributionValue


@statisticalTest
def _testCompareSnapshots(riplThunk):
    v,_,_,queryExps = betaModel(riplThunk())
    if ignore_inference_quality():
        samples = default_num_samples()
        runs = 2
    else:
        samples = 2 * int(math.sqrt(2 * default_num_samples()))
        runs = int(math.sqrt(2 * default_num_samples()))
    model = Analytics(v,queryExps=queryExps)
    history,_ = model.runFromConditional(samples,runs=runs)
    # two final snapshots should be very similar in distribution
    report = history.compareSnapshots(probes = (-2,-1))
    return report.statsDict['p']['KSSameContinuous']

def testCompareSnapshots():
    riplThunks = (get_ripl, lambda: get_mripl(no_ripls=4))
    for riplThunk in riplThunks:
        yield _testCompareSnapshots, riplThunk

def _testForce(riplThunk):
    v = riplThunk()
    for i in range(5):
        v.assume('x%i'%i,'(normal 0 100)')
    for _ in range(4):
        v.observe('(normal (+ x0 x1) 30)',100.)
    model = Analytics(v)
    samples = default_num_samples()
    inferProg = '(mh default one 1)'
    fdict = dict( [('x%i'%i,0) for i in range(5)] )
    history,_ = model.runFromConditional(samples,runs=5,simpleInfer=True,
                                         infer=inferProg,force=fdict)
    return history

def _testAtomType(conditional_prior):
    # make sure Analytics isn't confusing atoms with numbers
    v = get_ripl()
    v.observe('(categorical (simplex 0.5 0.5))', 'atom<1>')
    model = Analytics(v)
    samples = 1
    if conditional_prior == 'conditional':
        history, _ = model.runFromConditional(samples)
    else:
        history, _ = model.runConditionedFromPrior(samples)
    assert all(-1 < logscore < 0 for logscore in snapshot_t(history, 'logscore', 0))

def testAtomType():
    for cond_prior in 'conditional', 'prior':
        yield _testAtomType, cond_prior

## FIXME resinstate geweks
def _testGewekeTest():
    params = generateMRiplParams(no_ripls=(2,3), backends=('puma','lite'),
                                 modes=(True,))  ## ONLY LOCAL
    results = []

    for (no_ripls, backend, mode) in params:
        v=MRipl(no_ripls,backend=backend,local_mode=mode)
        v.assume('mu','(normal 0 30)')
        v.observe('(normal mu 200)','0')
        model = Analytics(v)
        fwd,inf,_=model.gewekeTest(50,plot=False,useMRipl=True)
        muSamples= [h.nameToSeries['mu'][0].values for h in [fwd,inf] ]

        res = reportKnownContinuous( stats.norm(loc=0,scale=30).cdf,
                                      muSamples[0], descr='testGeweke')
        assert res.pval > .01
        results.append(res)

    return results
