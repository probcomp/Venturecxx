from collections import OrderedDict
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed

def plot_data(data, label, title='', color='orange'):
    data_to_render_curve = np.loadtxt("data_to_render_curve.csv")
    fig, ax = plt.subplots()
    ax.hist(data, normed=True, color=color, label=label, bins=30);
    pd.DataFrame({'True distribution': data_to_render_curve}).plot(
    kind='kde', ax=ax, linewidth=4, color='darkblue'
    )
    outside={'loc': 'upper left',  'bbox_to_anchor':(1, 1.055)}
    ax.legend(**outside)
    ax.grid(True)
    ax.set_xlabel('X')
    ax.set_ylabel('P(X)')
    fig.set_size_inches(3, 2)
    ax.set_title(title)
    ax.set_xlim(-12, 13)
    ax.set_ylim(0, 0.25)
    return fig, ax

def load_csv(path):
    return np.loadtxt(path)
def save_csv(path, data):
    return np.savetxt(path, data)

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
            save_csv,
            [vt.StringType(), vt.ArrayUnboxedType(vt.NumberType())],
            vt.NilType(),
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
    ripl.bind_foreign_inference_sp(
        'subarray',
        deterministic_typed(
            lambda a, i: a[0:int(i)],
            [
                vt.ArrayUnboxedType(vt.NumberType()),
                vt.NumberType(),
                vt.NumberType(),
            ],
            vt.ArrayUnboxedType(vt.NumberType()),
            min_req_args=1
        )
    )
