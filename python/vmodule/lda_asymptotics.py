import multiprocessing
#
from venture import shortcuts
from venture.vmodule.synthetic_LDA_unit import LDA
from venture.vmodule.venture_unit import produceHistories, plotAsymptotics


parameters = {'topics' : [4, 8], 'vocab' : 10, 'documents' : [8, 16, 32],
    'words_per_document' : [8, 16, 32]}
cpu_count = multiprocessing.cpu_count()


def runner(params):
    ripl = shortcuts.make_church_prime_ripl()
    return LDA(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)

# multiprocessing Pool MUST be created AFTER runner is defined
def multiprocessing_mapper(func, *args, **kwargs):
    pool = multiprocessing.Pool(cpu_count)
    return pool.map(func, *args, **kwargs)

def picloud_mapper(func, *args):
    import cloud
    jids = cloud.map(func, *args, _env='venture_dan')
    return cloud.result(jids)

histories = produceHistories(parameters, runner, verbose=False,
        mapper=picloud_mapper)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
