from venture.venturemagics.ip_parallel import mk_p_ripl
from venture.unit import *
import numpy as np



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

    # (add (bernoulli p) (bernoulli p)) = 1,2 with high probability
    queryValues = history.nameToSeries[queryExps[0]][0].values
    assert np.sum(queryValues) > len(queryValues) 

    return 
