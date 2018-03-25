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
import os
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
    #return - estimated_p * np.log(true_p/estimated_p)
    not_estimated_p = 1 - estimated_p
    not_true_p = 1 - true_p
    return true_p * (np.log(true_p) - np.log(estimated_p)) +\
        not_true_p * (np.log(not_true_p) - np.log(not_estimated_p))

def get_KL(samples):
    samples = np.asarray(samples)
    estimated_probabilities = [
        np.mean(samples[:,i])
        for i in range(samples.shape[1])
    ]
    kl = 0.
    for i in range(samples.shape[1]):
        kl+= compute_kl(
            estimated_probabilities[i],
            PROBABILITIES_FROM_REJECTION_SAMPLING[i]
        )
    return kl, {'Estimated-probabilities': estimated_probabilities}


def take_MC_step(ripl):
    ripl.execute_program('chosen_inf_prog()')
    return ripl.evaluate('get_diseases()')

def noisy_or_kl(ripl):
    diseases = [take_MC_step(ripl) for _ in range(100)]
    return get_KL(diseases)

def MSE_airline(ripl):
    ripl.execute_program('''
        define gp_posterior_predictive = mapv(
            (_) -> {run(sample(gp(${test_input})))},
            arange(number_of_curves)
        );
    ''')
    mse = ripl.evaluate('''
        MSE(test_output, get_predictive_mean(gp_posterior_predictive))
    ''')
    return mse, {'parameters': 'none-recorded'}

def prep_ripl(benchmark, inf_prog_name):
    ripl = shortcuts.make_lite_ripl()
    ipynb_dict = read_json(benchmark + '/demo.ipynb')
    model_prog, obs_prog, inf_prog = get_code_cells_from_notebook(ipynb_dict)
    # XXX convention: plugins need to be called plugins.py.
    if os.path.isfile(benchmark + '/plugins.py'):
        ripl.load_plugin(benchmark + '/plugins.py')
    ripl.execute_program(model_prog)
    ripl.execute_program(inf_prog)
    # XXX convention: SMC inf progs have to containt the string SMC. If the
    # inference program is doing SMC, then data is not observed at this stage.
    if 'SMC' in inf_prog_name:
        ripl.execute_program('resample(number_particles);')
        ripl.execute_program('reset_to_prior')
    else:
        ripl.execute_program(obs_prog)
    ripl.define('chosen_inf_prog', inf_prog_name)
    return ripl, model_prog, obs_prog, inf_prog


def run_for_n_iterations(ripl, inf_iterations):
    """Run inference for n iterations."""
    start_time = time.time()
    for _ in range(inf_iterations):
        ripl.execute_program('chosen_inf_prog()')
    return time.time() - start_time


def run_for_t_seconds(ripl, stopping_time):
    """Run inference for t seconds."""
    iterations = 0
    start_time = time.time()
    if stopping_time == 0:
        return 0
    while True:
        ripl.execute_program('chosen_inf_prog()')
        time_elapsed = time.time() - start_time
        if (time_elapsed > stopping_time + 1.) and (iterations==0):
            iterations = None
            break
        elif time_elapsed > stopping_time:
            iterations += 1
            break
        iterations += 1
    return iterations


def run_experiment(
        benchmark,
        inf_prog_name,
        metric,
        seed,
        inf_iterations=None,
        stopping_time=None
    ):
    """Run individual benchmark with pytest"""
    ripl, model_prog, obs_prog, inf_prog = prep_ripl(benchmark, inf_prog_name)

    if (inf_iterations is not None) and (stopping_time is None):
        timing = run_for_n_iterations(ripl, inf_iterations)
        iterations = inf_iterations
    elif (inf_iterations is None) and (stopping_time is not None):
        iterations = run_for_t_seconds(ripl, stopping_time)
        timing = stopping_time
    else:
        raise ValueError('')

    if iterations is not None:
        time_stamp = datetime.datetime.now().isoformat()
        measurement, learned_parameters = metric(ripl)
        result = OrderedDict([
            ('inf-prog-name'     , inf_prog_name),
            ('iterations'        , iterations),
            ('metric'            , metric.__name__),
            ('seed'              , seed),
            ('timing'            , timing),
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
    'SMC_SIR',
])
@pytest.mark.parametrize('inf_iterations', [2])
@pytest.mark.parametrize('metric', [extrapolation_inlier_mse])
@pytest.mark.parametrize('seed', range(1, 2))
def test_experiment_linear_regression_iterations(
        benchmark,
        inf_prog_name,
        inf_iterations,
        metric,
        seed
    ):
    """Benchmark linear regression with outliers."""
    run_experiment(
        benchmark,
        inf_prog_name,
        metric,
        seed,
        inf_iterations=inf_iterations,
    )


@pytest.mark.parametrize('benchmark', ['linear-regression-with-outliers'])
@pytest.mark.parametrize('inf_prog_name', [
    'single_site_mh',
    'lbfgs_with_gibbs',
    'loop_explicitly_over_random_choices',
    'hamiltonian_monte_carlo_with_gibbs',
    'SMC_SIR',
    'SMC_HMC_rejuvenation',
    'SMC_gradient_rejuvenation',
])
@pytest.mark.parametrize('stopping_time', [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 50, 100, 200])
@pytest.mark.parametrize('metric', [extrapolation_inlier_mse])
@pytest.mark.parametrize('seed', range(1, 51))
def test_experiment_linear_regression_timing(
        benchmark,
        inf_prog_name,
        stopping_time,
        metric,
        seed
    ):
    """Benchmark linear regression with outliers."""
    run_experiment(
        benchmark,
        inf_prog_name,
        metric,
        seed,
        stopping_time=stopping_time,
    )


####### noisy-or ########
@pytest.mark.parametrize('benchmark', ['noisy-or'])
@pytest.mark.parametrize('inf_prog_name', [
    'resimulation_mh',
    'single_site_mh',
    'single_site_gibbs',
    'block_gibbs',
])
@pytest.mark.parametrize('stopping_time', [0, 30, 60, 120])
@pytest.mark.parametrize('metric', [noisy_or_kl])
@pytest.mark.parametrize('seed', range(1, 51))
def test_experiment_noisy_or_timing(
        benchmark,
        inf_prog_name,
        stopping_time,
        metric,
        seed
    ):
    """Benchmark noisy-or."""
    run_experiment(
        benchmark,
        inf_prog_name,
        metric,
        seed,
        stopping_time=stopping_time,
    )


####### GP structure learning ########
@pytest.mark.parametrize('benchmark', ['gp-structure-learning'])
@pytest.mark.parametrize('inf_prog_name', [
    'resimulation_mh',
    'single_site_mh',
])
@pytest.mark.parametrize('stopping_time',
    60 * np.array([0, 2, 5, 10, 15, 30, 45, 60, 75, 90])
)
@pytest.mark.parametrize('metric', [MSE_airline])
@pytest.mark.parametrize('seed', range(1, 51))
def test_experiment_gp_structure_learning_timing(
        benchmark,
        inf_prog_name,
        stopping_time,
        metric,
        seed
    ):
    """Benchmark noisy-or."""
    run_experiment(
        benchmark,
        inf_prog_name,
        metric,
        seed,
        stopping_time=stopping_time,
    )
