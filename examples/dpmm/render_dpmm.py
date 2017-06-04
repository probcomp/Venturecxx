from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np

def compactification_map(items):
    """Given a set integers, return a bijection between them and the
smallest prefix of the integers that admits such.

    The bijection is represented as a dict whose keys are input elements.

    The returned bijection preserves order of first appearance in the
    input, not value order.
    """
    ans = {}
    cur_idx = 0
    for item in items:
        if item not in ans:
            ans[item] = cur_idx
            cur_idx += 1
    return ans

def compactify(items):
    d = compactification_map(items)
    return [d[i] for i in items]

def inverse(permutation):
    """Return the inverse of the given permutation.

    For this purpose, a permutation on n elements is represented as a
    length-n array of the integers from 0 to n-1."""
    inv = [0] * len(permutation)
    for (i, x) in enumerate(permutation):
        inv[x] = i
    return inv

def remap_by_rep_count(items):
    """Permutes the values of the given items s.t. less common items get smaller values.

    output[i] == output[j] iff input[i] == input[j].

    In the output, 0 occurs no more than 1, which occurs no more than
    2, etc.

    Assumes the items consist of all the integers in [0, k)
    (presumably repeated).
    """
    rep_counts = OrderedDict()
    for item in items:
        if item in rep_counts:
            rep_counts[item] += 1
        else:
            rep_counts[item] = 1
    uniq = rep_counts.keys()
    # The sorted list of unique elements of items is (by assumption)
    # the identity permutation.
    remapping = inverse(sorted(uniq, key=rep_counts.__getitem__, reverse=True))
    return [remapping[i] for i in items]

def render_dpmm(lw_trace, row_names=None, col_names=None, selected_rows=None,
                show_assignments=False, show_V=False):
    ax = plt.gca()
    data = np.array([np.array(row_data) for row_data in lw_trace["data"]])
    assignments = np.array(lw_trace["assignments"])
    if selected_rows is not None:
        data = data[selected_rows]
        assignments = assignments[selected_rows]

    ax.set_xlim([-0.5, data.shape[1]-0.5])
    ax.set_ylim([-0.5, data.shape[0]-0.5])

    # make assignments in terms of cluster_idx, which go from 0, 1, 2, .., k-1
    assignments = np.array(compactify(assignments))

    # sort cluster assignments by size
    assignments = np.array(remap_by_rep_count(assignments))

    row_indexes = np.argsort(assignments, kind='mergesort')
    data = data[row_indexes, :]
    num_rows, num_cols = data.shape
    cluster_boundaries = (assignments[row_indexes][:-1] !=
                          assignments[row_indexes][1:]).nonzero()[0]
    for bd in cluster_boundaries:
        ax.plot([-0.5, num_cols-0.5], [bd+0.5, bd+0.5], color='magenta', linewidth=3)    
    ax.imshow(data, interpolation='None', cmap="YlGn", aspect='auto',
              vmin=np.percentile(data[:], 1), vmax=np.percentile(data[:], 99))

    ax.set_yticks(range(num_rows))
    if row_names is None:
        row_names = list(range(num_rows))
    row_names = np.array(row_names)
    row_indices = np.argsort(assignments, kind='mergesort')
    ax.set_yticklabels(row_names[row_indices], size='medium')

    assign_ticks = None
    if show_assignments:
        assign_ticks = ax.twinx()
        assign_ticks.set_ylim([-0.5, num_rows-0.5])
        assign_ticks.set_yticks(range(num_rows))
        assign_ticks.set_yticklabels(np.sort(assignments))
        assign_ticks.set_ylabel("Cluster assignments z(i)")

    ax.set_xticks(range(num_cols))
    if col_names is None:
        col_names = list(range(num_cols))
    col_names = np.array(col_names)
    ax.set_xticklabels(col_names, size='medium', rotation='vertical')

    hyper_labels = None
    alpha_text = None
    if show_V:
        hyper_labels = ax.twiny()
        hyper_labels.set_xlim([-0.5, num_cols-0.5])
        hyper_labels.set_xticks(range(num_cols))
        labels = ["V(%02d) = %.3f" % (i, v) for (i, v) in enumerate(lw_trace["V"])]
        hyper_labels.set_xticklabels(labels, rotation='vertical')
        if "alpha" in lw_trace:
            alpha_text = hyper_labels.set_xlabel("alpha: %5.3f" % (lw_trace["alpha"],))

    if "alpha" in lw_trace and not show_V:
        no_hyper_labels = ax.twiny()
        alpha_text = no_hyper_labels.set_xlabel("alpha: %5.3f" % (lw_trace["alpha"],))
        no_hyper_labels.set_xticks([])

    return (ax, alpha_text, hyper_labels, assign_ticks, inverse(row_indexes))
