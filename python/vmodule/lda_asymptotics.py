from venture import shortcuts
from venture.vmodule.synthetic_LDA_unit import LDA
from venture.vmodule.venture_unit import *


ripl = shortcuts.make_church_prime_ripl()
parameters = {'topics' : [4, 8], 'vocab' : 10, 'documents' : [8, 16, 32],
    'words_per_document' : [8, 16, 32]}
def runner(params):
    return LDA(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)
histories = produceHistories(parameters, runner)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
