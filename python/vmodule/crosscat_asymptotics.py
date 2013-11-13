# Copyright (c) 2013, MIT Probabilistic Computing Project.
# 
# This file is part of Venture.
# 	
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 	
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 	
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
import multiprocessing
#
from venture import shortcuts
from venture.vmodule.crosscat_unit import CrossCat
from venture.vmodule.venture_unit import produceHistories, plotAsymptotics


parameters = {'n_values': 2, 'n_rows': [8, 16], 'n_columns': [8, 16]}
cpu_count = multiprocessing.cpu_count()


def runner(params):
    ripl = shortcuts.make_church_prime_ripl()
    return CrossCat(ripl, params).runConditionedFromPrior(sweeps=20, runs=2)

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
