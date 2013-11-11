import multiprocessing
#
from venture import shortcuts
from venture.vmodule.synthetic_LDA_unit import LDA
from venture.vmodule.venture_unit import produceHistories, plotAsymptotics


parameters = {'topics' : [4, 8], 'vocab' : 10, 'documents' : [8, 16, 32],
    'words_per_document' : [8, 16, 32]}
cpu_count = multiprocessing.cpu_count()


ripl = shortcuts.make_church_prime_ripl()
def runner(params):
    return LDA(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)
# multiprocessing Pool MUST be created AFTER runner is defined
mapper = multiprocessing.Pool(cpu_count).map
histories = produceHistories(parameters, runner, verbose=False, mapper=mapper)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
