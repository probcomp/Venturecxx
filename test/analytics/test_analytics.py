from venture.venturemagics.ip_parallel import MRipl,mk_p_ripl
from venture.unit import *
import numpy as np
from nose.plugins.attrib import attr

@attr('slow')
def testAnalytics():
    
    # load ripl with model and observes
    # we use *add*,etc. because Analytics converts to Python values.
    v=mk_p_ripl()
    assumes=[('p','(beta 1.0 1.0)')] 
    observes=[('(flip p)',True) for _ in range(15)]
    for sym,exp in assumes:
        v.assume(sym,exp)
    for exp,literal in observes:
        v.observe(exp,literal)
    queryExps = ['(add (bernoulli p) (bernoulli p))']
    
    # run inference
    totalSamples=400
    inferredPValues = []
    for _ in range(totalSamples):
        v.infer(5)
        inferredPValues.append(v.report(1))
    
    # load model to Analytics and test __init__
    model = Analytics(v,queryExps=queryExps)
    assert model.backend==v.backend()
    assert model.assumes==assumes
    assert model.observes==observes
    assert model.queryExps==queryExps

    ## Run inference in Analytics

    # test history
    history,outRipl = model.runFromConditional(totalSamples,runs=1)
    assert history.data == observes
    assert [sym in history.nameToSeries for sym,_ in assumes]
    assert [exp in history.nameToSeries for exp in queryExps]
    
    # test outRipl: should be similar to v
    assert outRipl.backend()==v.backend()
    assert .2 > abs(outRipl.report(1) - v.report(1)) # inferred p's are close
    
    # test inference (FIXME: add stats test with (beta 1 16))
    analyticsPValues = history.nameToSeries['p'][0].values
    assert .1 > abs(np.mean(inferredPValues) - np.mean(analyticsPValues))
    assert .04 > abs(np.var(inferredPValues) - np.var(analyticsPValues))

    # (add (bernoulli p) (bernoulli p)) in [1,2] with high probability
    queryValues = history.nameToSeries[queryExps[0]][0].values
    assert np.sum(queryValues) > len(queryValues) 

    return 


def generateMRiplParams(backends=('puma','lite'),no_ripls=(2,3)):
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
        assert .5 > abs( np.mean(snapshot(lstMuValues,-1)) - trueMu)
        assert .6 > abs( np.std(snapshot(lstMuValues,-1)) )

        # mean over all samples close to trueMu
        assert .4 > abs(np.mean(lstMuValues)-trueMu)

        # test queryExps, i.e. mu^2
        lstQueryValues = [s.values for s in history.nameToSeries[queryExps[0]]]
        assert .001 > abs(np.mean(lstQueryValues - (np.array(lstMuValues)**2)) )
    ## test: runFromConditional
    totalSamples = 100
    runs = 2
    historyRFC,outMRipl = model.runFromConditional(totalSamples,runs=runs)
    testHistory(1,historyRFC)

    ## test: runConditionedFromPrior
    totalSamples = 140
    runs = 3
    historyRCP,_ = model.runConditionedFromPrior(totalSamples,runs=runs)
    trueMu = historyRCP.groundTruth['mu']['value']
    testHistory(trueMu,historyRCP)

    ## test: testFromPrior
    totalSamples = 40
    noDatasets = 5
    historyOV,_ = model.testFromPrior(noDatasets,totalSamples)
    lstMuValues = [s.values for s in historyOV.nameToSeries['mu']]
     # final samples close to prior on mu
    print abs( np.mean(snapshot(lstMuValues,-1) ) )
    print abs( np.std(snapshot(lstMuValues,-1)) - 2. )
    assert .8 > abs( np.mean(snapshot(lstMuValues,-1) ) )
    assert 1 > abs( np.std(snapshot(lstMuValues,-1)) - 2. )
    

def testBasicMRipl():
    for (no_ripls,backend,mode) in generateMRiplParams():
        _testBasicMRipl( MRipl(no_ripls,backend=backend,local_mode=mode) )
    return



    
    
    
    
