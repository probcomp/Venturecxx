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

"""MCDF and expanded state space CDFs.

This module addresses the problem of cumulative distribution functions
for distributions with atoms.  Two concepts are relevant:

- An mcdf (for CDF with Mass) on an ordered space X is
  a function: x -> (float, float).  The first float is the
  probability mass that is strictly less than x, and the second float
  is the mass at exactly x.  A traditional continuous cdf reports the
  second float as always zero.

- The expanded state space for a space X is X * [0,1], ordered
  lexicographically.  The idea is that a distribution on X that has
  atoms can be converted to a distribution on the expanded space with
  no atoms, by allowing anything that used to be an atom to gain
  probability continuously over the associated interval.
"""

import bisect
import itertools

def empirical_cdf(sample):
  """Return an MCDF for the given sample.

  [a] -> (a -> (float, float))"""
  step = 1.0 / len(sample)
  ordered = sorted(sample)
  def mcdf(x):
    low_ind = bisect.bisect_left(ordered, x)
    high_ind = bisect.bisect_right(ordered, x)
    return (low_ind * step, (high_ind - low_ind) * step)
  return mcdf

def discrete_cdf(rates):
  """Convert an explicit discrete distribution to its MCDF (by partial sums).

  (Eq a, Ord a) => [(a, float)] -> (a -> (float, float))"""
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
  """Convert a CDF to an MCDF assuming no atoms

  (a -> float) -> (a -> (float, float))."""
  def mcdf(x):
    return (cdf(x), 0)
  return mcdf

def expand_state_space(mcdf):
  """Convert an MCDF into a CDF on the expanded state space."""
  def expanded((x, portion)):
    (below, at) = mcdf(x)
    return below + portion * at
  return expanded

def deduplicate(sample):
  """Convert a sample with potential duplicates into a sample on the
expanded state space without duplicates.

  Duplicates in the original sample are spaced out along the extra intervals.
  """
  def chunk((x, xs)):
    k = len(list(xs))
    return [(x, float(i)/k) for i in range(k)]
  return list(itertools.chain.from_iterable(
    map(chunk, itertools.groupby(sorted(sample)))))

