# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 MIT Probabilistic Computing Project

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed

def is_square(integer):
    root = np.sqrt(integer)
    if int(root + 0.5) ** 2 == integer:
        return True
    else:
        return False

def plot_one_digit_mnist(data_vector, ax):
    """
    code taken and modified from here.
    """
    data_vector = np.asarray(data_vector)
    image_width = int(np.sqrt(data_vector.shape[0]))
    image = np.reshape(data_vector, (image_width, image_width))
    imgplot = ax.imshow(image, cmap='Greys')
    imgplot.set_interpolation('nearest')
    ax.xaxis.set_ticks_position('top')
    ax.yaxis.set_ticks_position('left')
    ax.set_xticks([], [])
    ax.set_yticks([], [])

def plot_mnist_data(data_vectors, title=None):
    index = 0
    if is_square(len(data_vectors)):
        len_square = int(np.sqrt(len(data_vectors)))
    else:
        raise ValueError('Plotting only supported for a square number of digis')
    fig, axes = plt.subplots(len_square, len_square);
    for i in range(len_square):
        for j in range(len_square):
            plot_one_digit_mnist(data_vectors[index], axes[i, j])
            index+=1

    fig.set_size_inches(6, 6)
    if title is not None:
        fig.suptitle(title, fontsize=20)
    return fig

def normalize(column):
    """Normalize a column so it's values are between -1 and 1."""
    if not column.any(): # check if all items are zero
        return np.ones(column.shape) * -1
    return np.asarray([float(i)/max(column) for i in column]) * 2 - 1

def load_csv(path):
    return pd.read_csv(path).values

def load_normalized(path):
    df =  pd.read_csv(path, header=None, delimiter=' ')
    for col in df.columns:
        df[col] = normalize(df[col].values)
    return df.values

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
        'load_normalized',
        deterministic_typed(
            load_normalized,
            [vt.StringType()],
            vt.ArrayUnboxedType(vt.ArrayUnboxedType(vt.NumberType())),
            min_req_args=1
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
