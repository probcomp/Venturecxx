# Copyright (c) 2013-2018 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import glob
import pytest
import time
import datetime
from collections import OrderedDict

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

from benchmark_utils import dump_json
from benchmark_utils import get_code_cells_from_notebook
from benchmark_utils import mkdir
from benchmark_utils import mse
from benchmark_utils import read_json

from run_benchmarks import prep_ripl
from benchmark_utils import mkdir

@pytest.mark.parametrize('inf_prog_name', [
    #'importance_sampling',
    'sequential_monte_carlo_after_step_5',
    'sequential_monte_carlo_resampling_at_end_only',
    'sequential_monte_carlo_every_step',
    ])
@pytest.mark.parametrize('number_traces_key', [0])
@pytest.mark.parametrize('seed', range(1, 21))
def test_assess_inference(
        inf_prog_name,
        number_traces_key,
        seed,
    ):
    ripl, model_prog, obs_prog, inf_prog = prep_ripl(
        seed,
        'hmm',
        inf_prog_name,
        smc_only = True
    )

    number_traces = {
        'sequential_monte_carlo_after_step_5': [50],
        'sequential_monte_carlo_resampling_at_end_only': [50],
        'sequential_monte_carlo_every_step': [50],
    }
    ripl.define('number_traces', number_traces[inf_prog_name][number_traces_key])
    start = time.time()
    if 'sequential_monte_carlo' in inf_prog_name:
        ripl.execute_program('%s()' % (inf_prog_name))
    elif inf_prog_name=='single_site_mh' or inf_prog_name=='resimulation_mh':
        ripl.execute_program(obs_prog)
        for _ in range(number_traces[inf_prog_name][number_traces_key]): # hack -- bad naming.
            ripl.execute_program('%s()' % (inf_prog_name))
    else:
        ripl.execute_program(obs_prog)
        ripl.execute_program('%s()' % (inf_prog_name))
    stopping_time = time.time() - start

    log_joint = ripl.evaluate('log_joint_at(default, all)')[0]
    log_lik = ripl.evaluate('log_likelihood_at(default, all)')[0]
    latents = ripl.evaluate('get_latents()')

    time_stamp = datetime.datetime.now().isoformat()
    result = OrderedDict([
        ('inf-prog-name'     , inf_prog_name),
        ('iterations'        , None),
        ('seed'              , seed),
        ('timing'            , stopping_time),
        ('measurement'       , log_lik),
        ('log_joint'         , log_joint),
        ('time-stamp'        , time_stamp),
        ('model-prog'        , model_prog),
        ('obs-prog'          , obs_prog),
        ('inf-prog'          , inf_prog),
        ('number-traces'     , ripl.evaluate('number_traces')),
        ('latents'           , latents),
    ])
    path_results_dir = 'hmm/results/'
    mkdir(path_results_dir)
    dump_json(result, path_results_dir + 'result-%s.json' % (time_stamp,))

@pytest.mark.parametrize('seed', range(10**5))
def test_rejection_sampling(
        seed,
    ):
    """Compute posterior probabilities for traces with rejection sampling"""
    ripl, model_prog, obs_prog, inf_prog = prep_ripl(
        seed,
        'hmm',
        'predict_latents()',
        smc_only = True
    )
    latents   = ripl.evaluate('predict_latents()')
    emissions = ripl.evaluate('sample_emissions()')
    dump_json(
        {'latents':latents, 'emissions':emissions},
        'hmm/rejection-sampling/sample-%d.json' % (seed,)
    )
