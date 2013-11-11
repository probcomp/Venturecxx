from venture import shortcuts
from venture.vmodule.crosscat_unit import CrossCat
from venture.vmodule.venture_unit import *


ripl = shortcuts.make_church_prime_ripl()
parameters = {'n_values': 2, 'n_rows': [16, 32, 64], 'n_columns': [16, 32, 64]}
def runner(params):
    return CrossCat(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)
histories = produceHistories(parameters, runner)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
