import multiprocessing
#
from venture import shortcuts
from venture.vmodule.crosscat_unit import CrossCat
from venture.vmodule.venture_unit import produceHistories, plotAsymptotics


parameters = {'n_values': 2, 'n_rows': [8, 16, 32], 'n_columns': [8, 16, 32]}
cpu_count = multiprocessing.cpu_count()


ripl = shortcuts.make_church_prime_ripl()
def runner(params):
    return CrossCat(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)
# multiprocessing Pool MUST be created AFTER runner is defined
mapper = multiprocessing.Pool(cpu_count).map
histories = produceHistories(parameters, runner, verbose=False, mapper=mapper)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
