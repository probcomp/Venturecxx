# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

"""Support for making p-p plots."""

import bisect
import itertools

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

# Returns a "massive cdf": a function a -> (Double, Double) that
# returns the total probability mass strictly below a, and the total
# mass of a itself.  A traditional cdf is equivalent to a massive cdf
# that always claims the mass at a is zero.
def empirical_cdf(sample):
  step = 1.0 / len(sample)
  ordered = sorted(sample)
  def mcdf(x):
    low_ind = bisect.bisect_left(ordered, x)
    high_ind = bisect.bisect_right(ordered, x)
    return (low_ind * step, (high_ind - low_ind) * step)
  return mcdf

def discrete_cdf(rates):
  # (Eq a, Ord a) => [(a, Double)] -> (a -> (Double, Double))
  # Convert an explicit discrete distribution to its "massive cdf" (by partial sums).
  ordered = sorted(rates, key=lambda (v, p): v)
  def mcdf(x):
    total = 0
    for (v, p) in ordered:
      if v < x: total += p
      if v == x: return (total, p)
      if v > x: return (total, 0)
    return (total, 0)
  return mcdf

def massless(cdf):
  # (a -> Double) -> (a -> (Double, Double))
  # Convert a traditional cdf to a "massive" one, assuming every
  # object has 0 mass.
  def mcdf(x):
    return (cdf(x), 0)
  return mcdf

# Convert a "massive cdf" into a cdf on an expanded state space.  The
# expanded state space is the product of the original state space with
# the interval [0,1], interpreting points with mass as gaining mass
# linearly over that interval.
def expand_state_space(mcdf):
  def expanded((x, portion)):
    (below, at) = mcdf(x)
    return below + portion * at
  return expanded

# Convert a sample with potential duplicates into a sample on the
# expanded state space without duplicates.  Duplicates in the original
# sample are spaced out along the extra intervals.
def deduplicate(sample):
  def chunk((x, xs)):
    k = len(list(xs))
    return [(x, i/k) for i in range(k)]
  return list(itertools.chain.from_iterable(
    map(chunk, itertools.groupby(sorted(sample)))))

def _p_p_plot(expected_massive, observed, ax):
  points = sorted(deduplicate(observed))
  cdf1 = expand_state_space(expected_massive)
  cdf2 = expand_state_space(empirical_cdf(observed))
  ax.plot([0,1], [0,1], 'r-', label="equality line")
  ax.scatter(map(cdf1, points), map(cdf2, points), label="observed")
  ax.legend()
  ax.set_xlabel("Probability")
  ax.set_ylabel("Probability (%s samples)" % len(observed))
  ax.set_title("Probability-probability plot", loc='left')

def p_p_plot(expected, observed, ax=None, show=False):
  if ax is None:
    ax = plt.axes()
  _p_p_plot(massless(expected), observed, ax)
  (K, pval) = stats.kstest(observed, expected)
  ax.set_title("One-sided K-S stat: %s, p-value: %s" % (K, pval), loc='right')
  if show:
    plt.show()
  return ax

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def count_occurrences(expectedRates, observed):
  items = [pair[0] for pair in expectedRates]
  itemsDict = {pair[0]:pair[1] for pair in expectedRates}
  for o in observed:
    assert o in itemsDict, "Completely unexpected observation %r" % o
    assert itemsDict[o] > 0, "Detected observation with expected probability 0 %r" % o
  # N.B. This is not None test allows observations to be selectively
  # ignored.  This is useful when information about the right answer
  # is incomplete.
  counts = [observed.count(x) for x in items
            if itemsDict[x] is not None and itemsDict[x] > 0]
  total = sum(counts)
  expRates = normalizeList([pair[1] for pair in expectedRates
                            if pair[1] is not None and pair[1] > 0])
  expCounts = [total * r for r in expRates]
  return (counts, expCounts)

def discrete_p_p_plot(expectedRates, observed, ax=None, show=False):
  if ax is None:
    ax = plt.axes()
  _p_p_plot(discrete_cdf(expectedRates), observed, ax)
  (counts, expCounts) = count_occurrences(expectedRates, observed)
  (chisq, pval) = stats.chisquare(counts, np.array(expCounts))
  ax.set_title("One-sided Chi^2 stat: %s\np-value: %s" % (chisq, pval), loc='right')
  if show:
    plt.show()
  return ax

def p_p_plot_2samp(observed1, observed2, ax=None, show=False):
  if ax is None:
    ax = plt.axes()
  dedup1 = deduplicate(observed1)
  dedup2 = deduplicate(observed2)
  points = sorted(dedup1 + dedup2)
  cdf1 = expand_state_space(empirical_cdf(observed1))
  cdf2 = expand_state_space(empirical_cdf(observed2))
  ax.plot([0,1], [0,1], 'r-', label="equality line")
  ax.scatter(map(cdf1, points), map(cdf2, points), label="observed")
  ax.legend()
  ax.set_xlabel("Probability (%s samples, observed1)" % len(observed1))
  ax.set_ylabel("Probability (%s samples, observed2)" % len(observed2))
  ax.set_title("Probability-probability plot", loc='left')
  (D, pval) = stats.ks_2samp(observed1, observed2)
  ax.set_title("Two-sided K-S stat: %s\np-value: %s" % (D, pval), loc='right')
  if show:
    plt.show()
  return ax

def show_example_plot(size=50, same=True):
  import math
  samp = stats.norm.rvs(size=size)
  if same is True:
    cdf = stats.norm(loc=0, scale=1).cdf
  else:
    cdf = stats.norm(loc=1, scale=math.sqrt(0.5)).cdf
  print samp
  p_p_plot(cdf, samp, show=True)

def show_example_plot_2samp(size=50, same=True):
  import math
  samp1 = stats.norm.rvs(size=size)
  if same is True:
    samp2 = stats.norm.rvs(size=size)
  else:
    samp2 = stats.norm.rvs(loc=1, scale=math.sqrt(0.5), size=size)
  print samp1, samp2
  p_p_plot_2samp(samp1, samp2, show=True)
