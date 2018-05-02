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

import os

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed

def get_filtering_dist(obs):
    """Compute the filtering distribution for a given HMM."""
    transition_matrix = np.asarray([
        [.6, .1, .1, .1, .1],
        [.1, .6, .1, .1, .1],
        [.1, .1, .6, .1, .1],
        [.1, .1, .1, .6, .1],
        [.1, .1, .1, .1, .6]
    ]);
    e = 0.01/4.;
    emission_matrix = np.asarray([
        [.99, e, e, e, e],
        [e, .99, e, e, e],
        [e, e, .99, e, e],
        [e, e, e, .99, e],
        [e, e, e, e, .99]
    ]);
    alphas = np.zeros((len(obs), 5))
    def alpha(t):
        if t == 0:
            return np.asarray([1, 0, 0, 0, 0])
        else:
            unnormalized = [emission_matrix[s, obs[t]] * sum([
                transition_matrix[s][s_minus_one] * alphas[t-1, s_minus_one]
                for s_minus_one in range(5)
                ])
                for s in range(5)
            ]
            return np.asarray(unnormalized)/np.linalg.norm(unnormalized)
    for t in range(len(obs)):
        alphas[t, :] = alpha(t)
    return alphas

def plot_single_trace(data, title, obs=False):
    """Create line plot to visualize a single trace."""
    if obs:
        variable = 'Emission'
    else:
        variable = 'State'
    data = [int(datum) for datum in data]
    fig, ax = plt.subplots()
    ax.plot(data, linestyle='--', marker='s');
    ax.grid(True)
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlim(-0.5, len(data) - 0.5)
    labels = [item.get_text() for item in ax.get_xticklabels()]
    ax.set_yticklabels(
        [''] + ['%s = %d' % (variable, i) for i in range(5)] + ['']
    )
    ax.set_xlabel('Time t')
    ax.set_title(title);
    fig.set_size_inches(6, 3)
    return fig, ax

def plot_single_trace_grid(data, title, obs=False):
    """Create grid plot to visualize a single trace."""
    if obs:
        variable = 'Emission'
    else:
        variable = 'State'
    data = [int(datum) for datum in data]
    fig, ax = plt.subplots()
    grid = get_grid(data)
    ax.imshow(grid, cmap='hot', interpolation='nearest')
    ax.set_xticks(range(len(data)))
    ax.set_yticklabels(
        reversed([''] + ['%s = %d' % (variable, i) for i in range(5)] + [''])
    )
    ax.set_xlabel('Time t')
    ax.set_title(title)
    return fig, ax


FONTSIZE = 16

def plot_marginal_given_data(data, title):
    """Plot a distribution on the marginal latents given samples."""
    grid = np.zeros((5, len(data[0])))
    for t in range(len(data[0])):
        unique, counts = np.unique(
            np.asarray(data)[:, t],
            return_counts=True
        )
        for i, value in enumerate(unique):
            grid[value, t] = float(counts[i])/len(data)
    return plot_marginal(grid.transpose(), title)

def plot_marginal(probabilities, title):
    """Plot a distribution on the marginal latents given probability values."""
    # Rotate array; needed for imshow
    grid = np.rot90(probabilities)
    fig, ax = plt.subplots()
    cax = ax.imshow(grid, cmap='plasma', interpolation='nearest')
    ax.set_xticks(range(grid.shape[1]))
    ax.set_yticklabels(
        reversed([''] + ['State = %d' % i for i in range(5)] + ['']),
        fontsize=FONTSIZE
    )
    ax.set_xlabel('Time t', fontsize=FONTSIZE)
    #ax.set_title(title)
    cb = plt.colorbar(cax,fraction=0.0238, pad=0.04)
    tick_locator = ticker.MaxNLocator(nbins=4)
    cb.locator = tick_locator
    cb.update_ticks()
    cb.ax.set_yticklabels(cb.ax.get_yticklabels(), fontsize=FONTSIZE)
    return fig, ax

def get_grid(data):
    grid = np.zeros((5, len(data)))
    for t, value in enumerate(data):
        grid[4 - value, t] = 1
    return grid

def load_csv(path):
    return np.loadtxt(path)

def __venture_start__(ripl):
    ripl.bind_foreign_inference_sp(
        'load_csv',
        deterministic_typed(
            load_csv,
            [vt.StringType()],
            vt.ArrayUnboxedType(vt.NumberType()),
            min_req_args=1
        )
    )
    ripl.bind_foreign_inference_sp(
        'save_csv',
        deterministic_typed(
            np.savetxt,
            [vt.StringType(), vt.ArrayUnboxedType(vt.NumberType())],
            vt.NilType(),
            min_req_args=2
        )
    )
    ripl.bind_foreign_inference_sp(
        'get_path',
        deterministic_typed(
            lambda: os.path.dirname(os.path.abspath(__file__)),
            [],
            vt.StringType(),
            min_req_args=0
        )
    )
    ripl.bind_foreign_inference_sp(
        'str_concat',
        deterministic_typed(
            lambda x,y: x + y,
            [vt.StringType(), vt.StringType()],
            vt.StringType(),
            min_req_args=2
        )
    )
