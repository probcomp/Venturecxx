from venture.venturemagics.ip_parallel import MRipl,mk_p_ripl
from venture.unit import *
import numpy as np
import scipy.stats as stats

from nose import SkipTest
from nose.plugins.attrib import attr
from venture.test.stats import statisticalTest, reportKnownContinuous

from venture.test.config import get_ripl,get_mripl,collectSamples
from testconfig import config

from nose.tools import eq_, assert_equal, assert_almost_equal


# def _testLoad(ripl_mripl):
#     v=ripl_mripl
#     assumes=[('p','(beta 1.0 1.0)')] 
#     observes=[('(flip p)',True) for _ in range(2)]
#     queryExps =  ['(add (bernoulli p) (bernoulli p))'] # exps must be in python form
#     [v.assume(sym,exp) for sym,exp in assumes]
#     [v.observe(exp,literal) for exp,literal in observes]
#     model = Analytics(v,queryExps=queryExps)
    
#     vBackend = v.backend if isinstance(v,MRipl) else v.backend()

#     def attributesMatch():
#         eq_( model.backend,vBackend )
#         eq_( model.assumes,assumes )
#         eq_( model.observes,observes )
#         eq_( model.queryExps,queryExps )
#     attributesMatch()

#     v.clear()
#     model = Analytics(v,assumes=assumes,observes=observes,queryExps=queryExps)
#     attributesMatch()

# def _testHistory(ripl_mripl):
#     v=ripl_mripl

# def testLoadRipl():
#     _testLoad(get_ripl())

# def testLoadMRipl():
#     _testLoad(get_mripl(no_ripls=3))

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
    stats,_ = compareSampleDicts(dicts,('',''),plot=False)
    assert stats['mu'][-1].pval > .01



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

    

def quickTests():
    testAnalytics(totalSamples=50)

    _testBasicMRipl( MRipl(2) )
    
    testSampleFromJointAssume()
    testSampleFromJointObserve()
    _testMRiplSampleFromJoint()
    _testMRiplRunFromJoint(samples=100)
    testCompareSampleDicts()
    testGewekeTest()
    return


def slowTests():
    testAnalytics()

    for (no_ripls,backend,mode) in generateMRiplParams():
        _testBasicMRipl( MRipl(no_ripls,backend=backend,local_mode=mode) )

    testSampleFromJointAssume()
    testSampleFromJointObserve()
    _testMRiplSampleFromJoint()
    _testMRiplRunFromJoint()
    testCompareSampleDicts()
    testGewekeTest()

    return

    
