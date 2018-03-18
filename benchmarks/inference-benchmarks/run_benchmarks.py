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

from collections import OrderedDict
import datetime
import pytest
import time

import numpy as np


from venture import shortcuts

from benchmark_utils import dump_json
from benchmark_utils import get_code_cells_from_notebook
from benchmark_utils import mkdir
from benchmark_utils import mse
from benchmark_utils import read_json


# Metrics are defined as follows: they return two outputs: (i) the actual
# measurements and (ii) optionally a dict with learned parameters.
def extrapolation_inlier_mse(ripl):
    """Compute mse (extrapolation) for inliers."""
    # Evaluate true parameters from notebook.
    max_xs = ripl.evaluate('max_xs')
    true_a = ripl.evaluate('true_a')
    true_b = ripl.evaluate('true_b')
    learned_a = ripl.sample('a')
    learned_b = ripl.sample('b')
    # Define the ground truth line.
    true_line = lambda x: true_a * x + true_b
    learned_line = lambda x: learned_a * x + learned_b
    n_test_points = 10
    test_xs = np.linspace(max_xs + 1, max_xs + n_test_points, n_test_points)
    target = true_line(test_xs)
    predictions = learned_line(test_xs)
    learned_params = {'a': learned_a, 'b': learned_b}
    return mse(target, predictions), learned_params


PROBABILITIES_FROM_REJECTION_SAMPLING = [
        0.03750426,
        0.03724874,
        0.9444865,
        0.02869364,
        0.02840974,
        0.02780407
]

def compute_kl(estimated_p, true_p):
    if estimated_p == 0.:
        print "warning"
        estimated_p = 0.00000001
    elif estimated_p == 1.:
        estimated_p = 1 - 0.00000001
    return - estimated_p * np.log(true_p/estimated_p)

def get_KL(samples):
    samples = np.asarray(samples)
    estimated_probabilities = [
        np.mean(samples[:,i])
        for i in range(samples.shape[1])
    ]
    print estimated_probabilities
    kl = 0.
    for i in range(samples.shape[1]):
        kl+= compute_kl(
            estimated_probabilities[i],
            PROBABILITIES_FROM_REJECTION_SAMPLING[i]
        )
    return kl, {'parameters': 'none-recorded'}

def noisy_or_kl(ripl):
    diseases = [ripl.evaluate('get_diseases()') for _ in range(100)]
    return get_KL(diseases)


def run_experiment(benchmark, inf_prog_name, inf_iterations, metric, seed):
    """Run individual benchmark with pytest"""
    ripl = shortcuts.make_lite_ripl()

    ipynb_dict = read_json(benchmark + '/demo.ipynb')
    model_prog, obs_prog, inf_prog = get_code_cells_from_notebook(ipynb_dict)
    ripl.execute_program(model_prog)
    ripl.execute_program(inf_prog)
    ripl.execute_program(obs_prog)
    ripl.define('chosen_inf_prog', inf_prog_name)

    start_time = time.time()
    for _ in range(inf_iterations):
        ripl.execute_program('chosen_inf_prog()')
    time_elaspsed = time.time() - start_time
    time_stamp = datetime.datetime.now().isoformat()
    measurement, learned_parameters = metric(ripl)
    result = OrderedDict([
        ('inf-prog-name'     , inf_prog_name),
        ('iterations'        , inf_iterations),
        ('metric'            , metric.__name__),
        ('seed'              , seed),
        ('timing'            , time_elaspsed),
        ('measurement'       , measurement),
        ('time-stamp'        , time_stamp),
        ('model-prog'        , model_prog),
        ('obs-prog'          , obs_prog),
        ('inf-prog'          , inf_prog),
        ('learned-parameters', learned_parameters),
    ])
    path_results_dir = benchmark + '/results/'
    mkdir(path_results_dir)
    dump_json(result, path_results_dir + 'result-%s.json' % (time_stamp,))


@pytest.mark.parametrize('benchmark', ['linear-regression-with-outliers'])
@pytest.mark.parametrize('inf_prog_name', [
    'single_site_mh',
    'lbfgs_with_gibbs',
    'loop_explicitly_over_random_choices',
    'hamiltonian_monte_carlo_with_gibbs'
])
@pytest.mark.parametrize('inf_iterations', range(11,31))
@pytest.mark.parametrize('metric', [extrapolation_inlier_mse])
@pytest.mark.parametrize('seed', range(1, 11))
def test_experiment_linear_regression(
        benchmark,
        inf_prog_name,
        inf_iterations,
        metric,
        seed
    ):
    """Benchmark linear regression with outliers."""
    run_experiment(benchmark, inf_prog_name, inf_iterations, metric, seed)

@pytest.mark.parametrize('benchmark', ['noisy-or'])
@pytest.mark.parametrize('inf_prog_name', [
    'resimulation_mh',
    'single_site_mh',
    'single_site_gibbs',
    #'particle_gibbs',
    'block_gibbs',
])
@pytest.mark.parametrize('inf_iterations', [10])
@pytest.mark.parametrize('metric', [noisy_or_kl])
@pytest.mark.parametrize('seed', range(1, 11))
def test_experiment_noisy_or(
        benchmark,
        inf_prog_name,
        inf_iterations,
        metric,
        seed
    ):
    """Benchmark linear regression with outliers."""
    run_experiment(benchmark, inf_prog_name, inf_iterations, metric, seed)
