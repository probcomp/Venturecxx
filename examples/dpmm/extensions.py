from collections import OrderedDict
import contextlib
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from venture.lite import types as t
from venture.lite import value as vv
from venture.lite.sp_help import deterministic_typed

self_dir = os.path.dirname(os.path.abspath(__file__))

@contextlib.contextmanager
def extra_load_paths(paths):
    abs_paths = [os.path.abspath(os.path.join(self_dir, p)) for p in paths]
    old_sys_path = sys.path
    try:
        sys.path = abs_paths + old_sys_path
        yield
    except Exception:
        sys.path = old_sys_path
        raise

with extra_load_paths(["."]):
    from render_dpmm import render_dpmm

def convert_from_venture_value(venture_value):
    """Convert a Venture data value to convenient python object."""
    if isinstance(venture_value, vv.VentureDict):
        shallow = t.Dict().asPythonNoneable(venture_value)
        deep = OrderedDict()
        for key, value in shallow.iteritems():
            deep[convert_from_venture_value(key)] = \
                convert_from_venture_value(value)
        return deep
    elif isinstance(venture_value, vv.VentureNumber):
        return venture_value.getNumber()
    elif isinstance(venture_value, vv.VentureInteger):
        return venture_value.getInteger()
    elif isinstance(venture_value, vv.VentureString):
        return venture_value.getString()
    elif isinstance(venture_value, vv.VentureBool):
        return venture_value.getBool()
    elif isinstance(venture_value, vv.VentureAtom):
        return venture_value.getAtom()
    elif isinstance(venture_value, vv.VentureArray):
        return [
            convert_from_venture_value(val)
            for val in venture_value.getArray()
        ]
    elif isinstance(venture_value, vv.VentureArrayUnboxed):
        return [
            convert_from_venture_value(val)
            for val in venture_value.getArray()
        ]
    elif isinstance(venture_value, vv.VentureMatrix):
        return venture_value.matrix
    elif isinstance(venture_value, vv.VenturePair):
        return [
            convert_from_venture_value(val)
            for val in venture_value.getArray()
        ]
    else:
        raise ValueError(
            'Venture value cannot be converted', str(venture_value))

def plot_histories(histories):
    unzipped = {}
    for h in histories:
        new = True
        for item in h:
            for (k, v) in item.iteritems():
                if k not in unzipped:
                    unzipped[k] = []
                if new:
                    unzipped[k].append([])
                unzipped[k][-1].append(v)
            new = False
    for (k, hs) in unzipped.iteritems():
        plt.figure()
        for h in hs:
            plt.plot(h)
        plt.xlabel("Inference iterations")
        plt.ylabel(k)
        plt.tight_layout()
        plt.savefig("results-%s.png" % (k,))
        plt.close()

def block_size(lw_trace):
    num_rows = len(lw_trace["assignments"])
    num_cols = len(lw_trace["V"])
    height = num_rows / 5 + 2.5
    width = 0.3 * num_cols + 1
    return (width, height)

def layout(samples):
    # I want
    # - Aspect ratio near 16:9
    # - Not too big, let's say less than 160 x 90 (inches)
    # - Fit as many samples as possible
    (block_width, block_height) = block_size(samples[0])
    max_width = max(int(math.floor(160 / block_width)), 1)
    max_height = max(int(math.floor(90 / block_height)), 1)
    max_capacity = len(samples)
    def layout_quality((width, height)):
        aspect_ratio = float(width * block_width)/float(height * block_height)
        discrepancy = abs(aspect_ratio - 16.0 / 9.0)
        capacity = width * height
        return -abs(max_capacity - capacity) - 3 * discrepancy
    return max([(w, h) for w in range(1, max_width) for h in range(1, max_height)],
               key = layout_quality)

def plot_samples(data, samples):
    (block_width, block_height) = block_size(samples[0])
    (width, height) = layout(samples)
    plt.figure(figsize=(block_width * width, block_height * height))
    for (i, lw_trace) in enumerate(samples):
        if i >= width * height: break
        plt.subplot(height, width, i + 1)
        lw_trace["data"] = data
        render_dpmm(lw_trace, show_assignments=True, show_V=True)
    plt.tight_layout()
    plt.savefig("results-samples.png")
    plt.close()

def make_plots(data, results):
    (histories, samples) = zip(*convert_from_venture_value(results))
    plot_histories(histories)
    plot_samples(data, samples)

make_plots_sp = deterministic_typed(make_plots, [t.Array(t.Array(t.Number)), t.Object], t.Nil)

def __venture_start__(ripl):
    ripl.bind_foreign_inference_sp("make_plots", make_plots_sp)
    ripl.bind_foreign_inference_sp('unique',
        deterministic_typed(lambda l: list(set(l)),
                        [t.HomogeneousListType(t.ExpressionType())],
                        t.HomogeneousListType(t.ExpressionType())))
