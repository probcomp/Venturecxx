import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr

import pandas as pd

import venture.lite.types as t
from venture.lite.builtin import deterministic_typed

def array_from_dataset(d):
    [ind_name] = d.ind_names
    yss = d.data[ind_name]
    return map(t.VentureValue.fromStackDict, yss)

def plot_lines(xs, yss, data_xs, data_ys, ymin, ymax, huemin, huemax, linewidth):
    hues = np.linspace(huemin, huemax, len(yss))
    fig, ax = plt.subplots(1)
    for (ys, hue) in zip(yss, hues):
        ax.plot(xs, ys, color=clr.hsv_to_rgb(np.array([hue, 1, 1]).reshape((1,1,3))).reshape(3), linewidth=linewidth)
    ax.scatter(data_xs, data_ys, color='k')
    ax.set_ylim(ymin, ymax)
    plt.show()
    # plt.savefig('plotlines_fig.png')

def __venture_start__(ripl):
    array_from_dataset_sp = deterministic_typed(array_from_dataset,
            [t.ForeignBlobType()],
            t.ArrayType())
    ripl.bind_foreign_inference_sp('array_from_dataset', array_from_dataset_sp)
    plot_lines_sp = deterministic_typed(plot_lines,
            [t.HomogeneousArrayType(t.NumberType()), # xs
                t.HomogeneousArrayType(t.HomogeneousArrayType(t.NumberType())), # yss
                t.HomogeneousArrayType(t.NumberType()), # data_xs
                t.HomogeneousArrayType(t.NumberType()), # data_ys
                t.NumberType(), # ymin
                t.NumberType(), # ymax
                t.NumberType(), # huemin
                t.NumberType(), # huemax
                t.NumberType(), # linewidth
                ],
            t.NilType())
    ripl.bind_foreign_inference_sp('plot_lines', plot_lines_sp)
