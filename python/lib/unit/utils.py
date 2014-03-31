import itertools
from collections import OrderedDict, namedtuple

def makeIterable(obj):
    return obj if hasattr(obj, '__iter__') else [obj]

def cartesianProduct(keyToValues):
    """:: {a: [b]} -> [{a: b}]"""
    items = [(key, makeIterable(value)) for (key, value) in keyToValues.items()]
    (keys, values) = zip(*items) if len(keyToValues) > 0 else ([], [])
    return [OrderedDict(zip(keys, t)) for t in itertools.product(*values)]

def productMap(parameters, runner, processes=None):
    """:: {a: [b]} -> ({a: b} -> c) -> {namedtuple a b : c}  (multiplying out the [b] over all a)

Given a dict defining spaces of possible parameter values, and a
parameterized function, returns a dict from all combinations of
parameter values to results of running that function on them.
Presumably, the function accepts parameters and returns a venture
unit History object.  For example, runner = lambda params :
Model(ripl, params).runConditionedFromPrior(sweeps, runs, track=0)

If the processes argument is not None, use that many worker
processes, running the parameter settings in parallel.
Unfortunately, this seems to require the function to run be defined
at the top level.  Why?

The answers are keyed by a namedtuple object because normal Python
dicts cannot appear as keys in Python dicts."""
    parameters_product = cartesianProduct(parameters)
    if processes is None:
        results = [runner(params) for params in parameters_product]
    else:
        from multiprocessing import Pool
        pool = Pool(int(processes))
        results = pool.map(runner, parameters_product)

    Key = namedtuple('Key', parameters_product[0].keys())
    hashable_keys = [Key._make(params.values()) for params in parameters_product]
    return dict(zip(hashable_keys, results))

