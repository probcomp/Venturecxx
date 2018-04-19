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

import os
import matplotlib.pyplot as plt
import numpy as np

import venture.lite.types as vt
import venture.lite.value as vv
from venture.lite.sp_help import deterministic_typed

def plot_parameter_dist(samples, title, xlabel):
    fig, ax = plt.subplots()
    ax.hist(samples, bins=10, label='Samples')
    true_param = np.loadtxt(
        os.path.dirname(os.path.abspath(__file__)) + '/' + xlabel + '.csv'
    )
    ax.axvline(x=true_param, linewidth=5, color='red', label='Ground truth')
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.grid(True)
    fig.set_size_inches(6,3)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1.037))
    return fig, ax

def plot_sampled_trace(data_xs, data_ys, outliers, a, b, std, outlier_std):
    fig, ax = plt.subplots()
    data_xs = np.asarray(data_xs)
    data_ys = np.asarray(data_ys)
    outliers = np.asarray(outliers)
    line_x = np.linspace(0, 15, 100)
    ax.plot(line_x, a * line_x + b, label='Sampled line', color='black')
    ax.plot(line_x, a * line_x + b - std, label='Inlier std', color='black', linestyle='--')
    ax.plot(line_x, a * line_x + b + std, color='black', linestyle='--')
    #ax.plot(line_x, a * line_x + b - outlier_std, label='Outlier std', color='red', linestyle='--')
    #ax.plot(line_x, a * line_x + b + outlier_std, color='red', linestyle='--')
    ax.scatter(
        data_xs[~outliers], data_ys[~outliers], label='Assigned inlier',
        color='green', marker='o', s=50, zorder=2
    )
    ax.scatter(data_xs[outliers], data_ys[outliers], label='Assigned outlier',
        color='red', marker='o', s=50, zorder=2
        )
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(1, 1.025),
        ncol=1,
        fontsize=12
    )
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_xlim([-0.5, 15.5])
    ax.set_ylim([-20, 60])
    fig.tight_layout()
    fig.set_size_inches(5, 4)
    ax.grid(True)
    ax.set_title('Sampled trace')
    return fig, ax

def plot_training_data(data_xs, data_ys):
    fig, ax = plt.subplots()
    data_xs = np.asarray(data_xs)
    data_ys = np.asarray(data_ys)
    outliers = np.loadtxt("outliers.csv").astype(bool)
    ax.scatter(data_xs[~outliers], data_ys[~outliers], label='Regular data', color='green', marker='+', s=100)
    ax.scatter(data_xs[outliers], data_ys[outliers], label='Outlier data', color='red', marker='x', s=100)
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(1, 1.025),
        ncol=3,
        fontsize=12
    )
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_xlim([0, 16])
    #ax.set_ylim([-100, 100])
    fig.tight_layout()
    fig.set_size_inches(5, 4)
    ax.grid(True)
    ax.set_title('Training data')
    return fig, ax

def generate_valid_symbol(index):
    return 'valid_symbol_%d' % (index,)

def __venture_start__(ripl):

    def shuffle(array):
        # Because of venture issue 306, I can't get Venture randseed directly
        # but I want shuffle to be deterministic nevertheless.
        np.random.seed(1)
        new_array = array # It seems that I have to do this, otherwise the array
        # is not mutable.
        np.random.shuffle(new_array)
        return new_array

    ripl.bind_foreign_inference_sp(
        'shuffle',
        deterministic_typed(
            shuffle,
            [vt.ArrayUnboxedType(vt.NumberType())],
            vt.ArrayUnboxedType(vt.NumberType()),
            min_req_args=1
        )
    )
    ripl.bind_foreign_inference_sp(
        'number_to_symbol',
        deterministic_typed(
            generate_valid_symbol,
            [vt.NumberType()],
            vt.SymbolType(),
            min_req_args=1
        )
    )
    ripl.bind_foreign_inference_sp(
        'load_csv',
        deterministic_typed(
            np.loadtxt,
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
        'save_boolean_csv',
        deterministic_typed(
            np.savetxt,
            [vt.StringType(), vt.ArrayUnboxedType(vt.BoolType())],
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

