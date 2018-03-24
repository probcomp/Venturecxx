import contextlib
from collections import OrderedDict
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed
from venture.lite.gp import _cov_sp
from venture.lite.gp import GPCovarianceType
from venture.lite.covariance import Kernel
from venture.lite.utils import override

class change_point(Kernel):
  """Change point between kernels K and H."""

  @override(Kernel)
  def __init__(self, location, scale, K, H):
    self._K = K
    self._H = H
    self._location = location
    self._scale = scale

  @override(Kernel)
  def __repr__(self):
    return 'CP(%r, %r)' % (self._K, self._H)

  @property
  @override(Kernel)
  def parameters(self):
    K_shape = ParamProduct(self._K.parameters)
    H_shape = ParamProduct(self._H.parameters)
    return [K_shape, H_shape]

  def _change(self, x, location, scale):
    return 0.5 *(1 + np.tanh((location-x)/scale))

  @override(Kernel)
  def f(self, X, Y):
    # XXX only works on one 1-d input.
    """ Implementing Lloyd et al., 2014, Appendix A2.

    CP(k,h) = sig_1 * k + sig_2 * h

    where

    sig_1 = change(x) * change(y) and

    sig_2 = (1 - change(x)) * (1 - change(y)).

    Note the use of lower case k and h above, to indicate actual kernels, that
    is covariance functions with scalar input.
    """
    K = self._K
    H = self._H

    change_x = self._change(X, self._location, self._scale)
    change_y = self._change(Y, self._location, self._scale)
    sig_1 = np.outer(change_x, change_y)
    sig_2 = np.outer(1 - change_x, 1 - change_y)
    return np.multiply(sig_1, K.f(X, Y)) + np.multiply(sig_2, H.f(X, Y))

  @override(Kernel)
  def df_theta(self, X, Y):
    raise NotImplementedError

  @override(Kernel)
  def df_x(self, x, Y):
    raise NotImplementedError

def load_csv(path):
    return np.loadtxt(path)

def get_figure_parameters(dict_of_plotting_parameters):
    if "alpha" in dict_of_plotting_parameters:
        alpha = dict_of_plotting_parameters["alpha"].getNumber()
    else:
        alpha = 1
    if "width" in dict_of_plotting_parameters:
        width = dict_of_plotting_parameters["width"].getNumber()
    else:
        width = None
    if "height" in dict_of_plotting_parameters:
        height  = dict_of_plotting_parameters["height"].getNumber()
    else:
        height = None
    if "color" in dict_of_plotting_parameters:
        color = dict_of_plotting_parameters["color"].getString()
    else:
        color = "green"
    if "marker" in dict_of_plotting_parameters:
        marker = dict_of_plotting_parameters["marker"].getString()
    else:
        marker = None
    if "linestyle" in dict_of_plotting_parameters:
        linestyle = dict_of_plotting_parameters["linestyle"].getString()
    else:
        linestyle = "-"
    if "markersize" in dict_of_plotting_parameters:
        markersize = dict_of_plotting_parameters["markersize"].getNumber()
    else:
        markersize = 200
    return width, height, linestyle, color, alpha, marker, markersize

def get_plot_labels(dict_of_plotting_parameters):
    if "label" in dict_of_plotting_parameters:
        label = dict_of_plotting_parameters["label"].getString()
    else:
        label = None
    if "title" in dict_of_plotting_parameters:
        title = dict_of_plotting_parameters["title"].getString()
    else:
        title = None
    if "xlabel" in dict_of_plotting_parameters:
        xlabel = dict_of_plotting_parameters["xlabel"].getString()
    else:
        xlabel = None
    if "ylabel" in dict_of_plotting_parameters:
        ylabel = dict_of_plotting_parameters["ylabel"].getString()
    else:
        ylabel = None
    if "xlim" in dict_of_plotting_parameters:
        xlim = [
            lim.getNumber()
            for lim in dict_of_plotting_parameters["xlim"].getArray()
        ]
    else:
        xlim = None
    if "ylim" in dict_of_plotting_parameters:
        ylim = [
            lim.getNumber()
            for lim in dict_of_plotting_parameters["ylim"].getArray()
        ]
    else:
        ylim = None
    return label, title, xlabel, ylabel, xlim, ylim

def create_figure(width, height):
    fig = plt.gcf()
    ax = plt.gca()
    if fig is None:
        fig, ax = plt.subplot()
    if (width is not None) and (height is not None):
        fig.set_size_inches(width, height)
    ax.grid(True)
    return fig, ax

def label_figure(ax, title, xlabel, ylabel, xlim, ylim):
    if title is not None:
        ax.set_title(title)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if xlim is not None:
        ax.set_xlim(xlim )
    if ylim is not None:
        ax.set_ylim(ylim )

def scatter_plot(x, y, dict_of_plotting_parameters={}):
    width, height, linestyle, color, alpha, marker, markersize =\
        get_figure_parameters(
            dict_of_plotting_parameters
        )
    label, title, xlabel, ylabel, xlim, ylim, = get_plot_labels(
        dict_of_plotting_parameters
    )
    fig, ax = create_figure(width, height)
    if marker is None:
        marker = 'x'
    ax.scatter(x, y, zorder=2, alpha=alpha, marker=marker,
        s=markersize, linewidths=2, color = color, label=label)
    label_figure(ax, title, xlabel, ylabel, xlim, ylim)

def line_plot(x, y, dict_of_plotting_parameters={}):
    width, height, linestyle, color, alpha, marker, markersize =\
        get_figure_parameters(
            dict_of_plotting_parameters
        )
    label, title, xlabel, ylabel, xlim, ylim, = get_plot_labels(
        dict_of_plotting_parameters
    )
    fig, ax = create_figure(width, height)
    if marker is None:
        ax.plot(
            x,
            y,
            linestyle=linestyle,
            color=color,
            alpha=alpha,
            label=label
        )
    else:
        ax.plot(
            x,
            y,
            linestyle=linestyle,
            marker=marker,
            color=color,
            alpha=alpha,
            label=label
        )
    label_figure(ax, title, xlabel, ylabel, xlim, ylim)

def legend(location=None):
    ax = plt.gca()
    handles, labels = ax.get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    legend_object = ax.legend(
        by_label.values(),
        by_label.keys(),
        frameon = 1,
        loc = location
    )
    for line in legend_object.get_lines():
        line.set_alpha(1)
    legend_object.get_frame().set_facecolor('white')

    os.path.dirname(os.path.abspath(__file__))

def __venture_start__(ripl):
    ripl.bind_foreign_inference_sp(
        'get_mean',
        deterministic_typed(
            np.mean,
            [
                vt.ArrayUnboxedType(vt.NumberType()),
            ],
            vt.NumberType(),
            min_req_args=1
        )
    )
    ripl.execute_program('''
        define get_squared_error = (target, prediction) -> {
            mapv(
                (i) -> {(lookup(target, i) - lookup(prediction, i))**2},
                arange(size(target))
            )
        };
        define MSE = (target, prediction) -> {
            get_mean(get_squared_error(target, prediction))
        };
    ''')
    ripl.bind_foreign_inference_sp(
        'get_predictive_mean',
        deterministic_typed(
            lambda x: np.mean(x, axis=0),
            [
                vt.ArrayUnboxedType(vt.ArrayUnboxedType(vt.NumberType())),
            ],
            vt.ArrayUnboxedType(vt.NumberType()),
            min_req_args=1
        )
    )
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
        'scatter_plot',
        deterministic_typed(
            scatter_plot,
            [
                vt.ArrayUnboxedType(vt.NumberType()),
                vt.ArrayUnboxedType(vt.NumberType()),
                vt.HomogeneousDictType(vt.StringType(), vt.AnyType())
            ],
            vt.NilType(),
            min_req_args=2
        )
    )
    ripl.bind_foreign_inference_sp(
        'line_plot',
        deterministic_typed(
            line_plot,
            [
                vt.ArrayUnboxedType(vt.NumberType()),
                vt.ArrayUnboxedType(vt.NumberType()),
                vt.HomogeneousDictType(vt.StringType(), vt.AnyType())
                ],
            vt.NilType(),
            min_req_args=2
        )
    )
    ripl.bind_foreign_inference_sp(
        'legend',
        deterministic_typed(
            legend,
            [vt.StringType()],
            vt.NilType(),
            min_req_args=0
        )
    )
    ripl.bind_foreign_sp(
        'gp_cov_cp',
        _cov_sp(
            change_point,
            [
                vt.NumberType(),
                vt.NumberType(),
                GPCovarianceType('K'),
                GPCovarianceType('H')
            ]
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
