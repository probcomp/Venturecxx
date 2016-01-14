# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

def p_p_plot_2samp(observed1, observed2, ax=None):
  if ax is None:
    ax = plt.axes()
  dedup1 = deduplicate(observed1)
  dedup2 = deduplicate(observed2)
  points = sorted(dedup1 + dedup2)
  cdf1 = expand_state_space(empirical_cdf(observed1))
  cdf2 = expand_state_space(empirical_cdf(observed2))
  ax.scatter(map(cdf1, points), map(cdf2, points))
  return ax
