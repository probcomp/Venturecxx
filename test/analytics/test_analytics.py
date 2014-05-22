from venture.venturemagics.ip_parallel import MRipl,mk_p_ripl
from venture.unit import *
import numpy as np
import scipy.stats as stats
from itertools import product

from nose import SkipTest
from nose.plugins.attrib import attr
from venture.test.stats import statisticalTest, reportKnownContinuous

from venture.test.config import get_ripl,get_mripl,collectSamples
from testconfig import config

from nose.tools import eq_, assert_equal, assert_almost_equal


## Functions used by tests
def betaModel(ripl):
    assumes=[('p','(beta 1.0 1.0)')] 
    observes=[('(flip p)',True) for _ in range(2)]
    queryExps =  ['(add (bernoulli p) (bernoulli p))'] # exps in python form
    [ripl.assume(sym,exp) for sym,exp in assumes]
    [ripl.observe(exp,literal) for exp,literal in observes]
    return ripl,assumes,observes,queryExps

def normalModel(ripl):
    assumes = [ ('x','(normal 0 100)') ]
    observes = [ ('(normal x 100)','0') ]
    queryExps = ('(* x 2)',)
    [ripl.assume(sym,exp) for sym,exp in assumes]
    [ripl.observe(exp,literal) for exp,literal in observes]
    xPriorCdf = stats.norm(0,100).cdf
    return ripl,assumes,observes,queryExps,xPriorCdf

def snapshot_t(history,name,t):
    return [series.values[t] for series in history.nameToSeries[name]]

def nameToFirstValues(history,name): return history.nameToSeries[name][0].values



## Tests
def _testLoadModel(ripl_mripl):
    v=ripl_mripl
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

def testLoad():
    yield _testLoadModel, get_ripl()
    yield _testLoadModel, get_mripl(no_ripls=3)
    

def _testHistory(ripl_mripl):
    v=ripl_mripl
    v,assumes,observes,queryExps = betaModel(v)
    samples = 5
    model = Analytics(v,queryExps=queryExps)
    history,_ = model.runFromConditional(samples,runs=1)
    eq_(history.data,observes)
    assert all( [sym in history.nameToSeries for sym,_ in assumes] )
    assert all( [exp in history.nameToSeries for exp in queryExps] )
    averageP = np.mean( history.nameToSeries['p'][0].values )
    assert_almost_equal(averageP,history.averageValue('p'))
    
def testHistory():
    yield _testHistory, get_ripl()
    yield _testHistory, get_mripl(no_ripls=3)

def _testRuns(ripl_mripl):
    v,assumes,observes,queryExps,_ = normalModel( ripl_mripl )
    samples = 20
    runsList = [2,3,7]
    model = Analytics(v,queryExps=queryExps)
    
    for no_runs in runsList:
        history,_ = model.runFromConditional(samples,runs=no_runs)
        eq_( len(history.nameToSeries['x']), no_runs)

        for exp in ('x', queryExps[0]):
            arValues = np.array([s.values for s in history.nameToSeries[exp]])
            assert all(np.var(arValues,axis=0) > .0001) # var across runs time t
            assert all(np.var(arValues,axis=1) > .000001) # var within runs 

def testRuns():
    yield _testRuns, get_ripl()
    yield _testRuns, get_mripl(no_ripls=3)




@statisticalTest
def _testInfer(ripl_mripl,conditional_prior,inferProg):
    v,_,_,_= betaModel( ripl_mripl ) 
    samples = 40
    runs = 20
    model = Analytics(v)

    if conditional_prior == 'conditional':
        history,_ = model.runFromConditional(samples,runs=runs,
                                             infer=inferProg)
        cdf = stats.beta(3,1).cdf
    else:
        history,_ = model.runConditionedFromPrior(samples,runs=runs,
                                                  infer=inferProg)
        dataValues = [typeVal['value'] for exp,typeVal in history.data] 
        noHeads = sum(dataValues)
        noTails = len(dataValues) - noHeads
        cdf = stats.beta(1+noHeads,1+noTails).cdf
        # will include gtruth (but it won't affect test)
        
    return reportKnownContinuous(cdf,snapshot_t(history,'p',-1))                                 
                                     
def testRunFromConditionalInfer():
    riplThunks = (get_ripl, lambda: get_mripl(no_ripls=3))
    cond_prior = ('conditional','prior')
    #k1 = {"transitions":1,"kernel":"mh","scope":"default","block":"all"}
    k1 = '(mh default one 1)'
    k2 = '(mh default one 2)'
    infProgs = ( None, k1,'(cycle (%s %s) 1)'%(k1,k2) )  

    params = product(riplThunks,cond_prior,infProgs)

    for r,c,i in params:
        yield _testInfer, r(), c, i



@statisticalTest        
def _testSampleFromJoint(riplThunk,useMRipl):
    v,assumes,observes,queryExps,xPriorCdf = normalModel( riplThunk() )
    samples = 30
    model = Analytics(v,queryExps=queryExps)
    history = model.sampleFromJoint(samples, useMRipl=useMRipl)
    xSamples = nameToFirstValues(history,'x')
    return reportKnownContinuous(xPriorCdf,xSamples)
    
def testSampleFromJoint():
    raise SkipTest("Maybe bug or old problem of identical samples on puma")
    riplThunks = (get_ripl, lambda: get_mripl(no_ripls=3))
    useMRiplValues = (True,False)
    params = product(riplThunks, useMRiplValues)
    for riplThunk,useMRipl in params:
        yield _testSampleFromJoint, riplThunk, useMRipl



@statisticalTest        
def _testRunFromJoint1(ripl_mripl,inferProg):
    v,assume,_,queryExps,xPriorCdf = normalModel( ripl_mripl)
    model = Analytics(v,queryExps=queryExps)
    # variation across runs
    history = model.runFromJoint(1, runs=30, infer=inferProg)
    return reportKnownContinuous(xPriorCdf,snapshot_t(history,'x',0))


@statisticalTest        
def _testRunFromJoint2(ripl_mripl,inferProg):
    v,assume,_,queryExps,xPriorCdf = normalModel( ripl_mripl)
    model = Analytics(v,queryExps=queryExps)

    # variation over single runs
    history = model.runFromJoint(200, runs=1, infer=inferProg)
    XSamples = np.array(nameToFirstValues(history,'x'))
    thinXSamples = XSamples[np.arange(0,200,20)]
    
    return reportKnownContinuous(xPriorCdf,thinXSamples)

def testRunFromJoint():
    raise SkipTest("Debugging problem with repeatTest and thunks")

    tests = (_testRunFromJoint1, _testRunFromJoint2)
    riplThunks = (get_ripl, lambda: get_mripl(no_ripls=3))
    infProgs = ( None, '(mh default one 5)')

    params = [(t,r,i) for t in tests for r in riplThunks for i in infProgs]

    for t,r,i in params:
        yield t,r(),i
    
    

    
        
    

# def _testInferRuns(ripl_mripl):
#     v=ripl_mripl
#     v.assume('x','(normal 1 1)')
#     queryExps = ['(pow x 2)']
#     model = Analytics(v,queryExps=queryExps)
#     history,outRipl = model.runFromConditional(20,runs=10)
    
# def oldAnalytics()
#     ## Run inference in Analytics
#     # test history
#     history,outRipl = model.runFromConditional(totalSamples,runs=1)
#     assert history.data == observes
#     assert [sym in history.nameToSeries for sym,_ in assumes]
#     assert [exp in history.nameToSeries for exp in queryExps]
    
#     # test outRipl: should be similar to v
#     assert outRipl.backend()==v.backend()
#     if totalSamples >= 400:
#         assert .5 > abs(outRipl.report(1) - v.report(1)) # inferred p's are close
    
#     # test inference (FIXME: add stats test with (beta 1 16))
#     analyticsPValues = history.nameToSeries['p'][0].values
#     if totalSamples >= 400:
#         assert .1 > abs(np.mean(inferredPValues) - np.mean(analyticsPValues))
#         assert .04 > abs(np.var(inferredPValues) - np.var(analyticsPValues))

#     # (add (bernoulli p) (bernoulli p)) in [1,2] with high probability
#     queryValues = history.nameToSeries[queryExps[0]][0].values
#     assert np.sum(queryValues) > len(queryValues) 

#     return 

def generateMRiplParams(backends=('puma','lite'),no_ripls=(2,3),modes=None):
    if modes is None:
        try:
            v=MRipl(2)
            modes=(True,False)
        except:
            modes=(False,)
    params = [(n,b,m) for n in no_ripls for b in backends for m in modes]
    return params

def _testBasicMRipl(mripl):
    v=mripl
    v.assume('mu','(normal 0 2)')
    num_obs = 8
    [v.observe('(normal mu .05)','1.') for _ in range(num_obs)]
    queryExps = ['(pow mu 2)']
    model = Analytics(v,queryExps=queryExps)

    # test outMRipl- currently will be unmutated because of how inference works

    # test History
    snapshot=lambda lstSeries,i: [s[i] for s in lstSeries]

    def testHistory(trueMu,history):
        lstMuValues = [s.values for s in history.nameToSeries['mu']]

        # final samples close to trueMu
        assert .7 > abs( np.mean(snapshot(lstMuValues,-1)) - trueMu)
        assert .6 > abs( np.std(snapshot(lstMuValues,-1)) )

        # mean over all samples close to trueMu
        assert .6 > abs(np.mean(lstMuValues)-trueMu)

        # test queryExps, i.e. mu^2
        lstQueryValues = [s.values for s in history.nameToSeries[queryExps[0]]]
        assert .001 > abs(np.mean(lstQueryValues - (np.array(lstMuValues)**2)) )
    ## test: runFromConditional
    totalSamples = 150
    runs = 1
    historyRFC,_ = model.runFromConditional(totalSamples,runs=runs)
    testHistory(1,historyRFC)

    ## test: runConditionedFromPrior
    totalSamples = 140
    runs = 2
    historyRCP,_ = model.runConditionedFromPrior(totalSamples,runs=runs)
    trueMu = historyRCP.groundTruth['mu']['value']
    testHistory(trueMu,historyRCP)

    ## test: testFromPrior
    totalSamples = 30
    noDatasets = 2
    historyOV,_ = model.testFromPrior(noDatasets,totalSamples)
    lstMuValues = [s.values for s in historyOV.nameToSeries['mu']]
     # final samples close to prior on mu
    assert 5 > abs(np.mean(snapshot(lstMuValues,-1)))
    

def testBasicMRipl():
    raise SkipTest("Doesn't run properly on Jenkins")
    'Test MRipl in local mode with puma and lite'
    params = generateMRiplParams(no_ripls=(2,),backends=('puma','lite'),modes=(False,) )
    for (no_ripls,backend,mode) in params:
        _testBasicMRipl( MRipl(no_ripls,backend=backend,local_mode=mode) )
    return


#### TEST RIPL SAMPLE FROM JOINT (FIXME currently failing)
def _sampleFromJointHistory():
    v=mk_p_ripl() 
    v.assume('mu','(normal 10 .01)')
    v.observe('(normal mu .01)','10')
    model = Analytics(v)
    samples = 50
    return  model.sampleFromJoint(samples)
    
#@statisticalTest
def testSampleFromJointAssume():
    history = _sampleFromJointHistory()
    muSamples = history.nameToSeries['mu'][0].values
    res= reportKnownContinuous(stats.norm(loc=10,scale=.01).cdf,
                                  muSamples, descr='testSampleFromJointAssume')
    #assert res.pval > .01
    return res
#@statisticalTest    
def testSampleFromJointObserve():
    history = _sampleFromJointHistory()
    nameObs= [k for k in history.nameToSeries.keys() if 'obs' in k][0]
    obsSamples = history.nameToSeries[nameObs][0].values
    res= reportKnownContinuous( stats.norm(loc=10,scale=.014).cdf,
                                  obsSamples, descr='testSampleFromJointObserve')
    #assert res.pval > .01
    return res


#@statisticaltest
def _testMRiplSampleFromJoint():
    params = generateMRiplParams(backends=('puma','lite'),modes=(True,False))
    results = []
    
    for (no_ripls, backend, mode) in params:

        v=MRipl(no_ripls,backend=backend,local_mode=mode)
        v.assume('mu','(normal 10 .01)')
        v.observe('(normal mu .01)','10')
        model = Analytics(v)
        samples = 25
        history = model.sampleFromJoint(samples,useMRipl=True)
        muSamples = history.nameToSeries['mu'][0].values
        resMu= reportKnownContinuous( stats.norm(loc=10,scale=.01).cdf,
                                      muSamples, descr='testMRiplSFJ')
        #assert resMu.pval > .01
        results.append(resMu)

    return results

#@statisticaltest
## FIXME: why do we fail remote runFromJoint?
def _testMRiplRunFromJoint(samples=500,runs=2):
    params = generateMRiplParams(no_ripls=(2,), backends=('puma',),#'lite'),
                                 modes=(True,False))
    results = []
    
    for (no_ripls, backend, mode) in params:
        v=MRipl(no_ripls,backend=backend,local_mode=mode)
        v.assume('mu','(normal 0 30)')
        v.observe('(normal mu 200)','0')
        model = Analytics(v)
        history = model.runFromJoint(samples,runs=runs,useMRipl=True)
        muSamples=[]
        for r in range(runs):
            muSamples.extend(history.nameToSeries['mu'][r].values)
        
        resMu= reportKnownContinuous( stats.norm(loc=0,scale=30).cdf,
                                      muSamples, descr='testMRiplIFJ')
        #assert resMu.pval > .01
        results.append(resMu)
    
    print 'pvals:',map(lambda x:x.pval,results)
    return results


def testCompareSampleDicts():
    v=mk_p_ripl() 
    v.assume('mu','(normal 10 .01)')
    v.observe('(normal mu .01)','10')
    model = Analytics(v)
    samples=20
    h,_ = model.runFromConditional(samples,runs=2) 
    dicts = [{'mu':h.nameToSeries['mu'][i].values} for i in range(2)]
    cReport = compareSampleDicts(dicts,('',''),plot=False)
    assert cReport.statsDict['mu']['KSSameContinuous'].pval > .01



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

    

# def quickTests():
#     testAnalytics(totalSamples=50)

#     _testBasicMRipl( MRipl(2) )
    
#     testSampleFromJointAssume()
#     testSampleFromJointObserve()
#     _testMRiplSampleFromJoint()
#     _testMRiplRunFromJoint(samples=100)
#     testCompareSampleDicts()
#     testGewekeTest()
#     return


# def slowTests():
#     testAnalytics()

#     for (no_ripls,backend,mode) in generateMRiplParams():
#         _testBasicMRipl( MRipl(no_ripls,backend=backend,local_mode=mode) )

#     testSampleFromJointAssume()
#     testSampleFromJointObserve()
#     _testMRiplSampleFromJoint()
#     _testMRiplRunFromJoint()
#     testCompareSampleDicts()
#     testGewekeTest()

#     return

    





