# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

from venture.lite.exception import VentureTypeError

def derivative(f, x):
  return lambda(h): (f(x+h) - f(x-h)) / (2*h)

def richardson_step(f, degree):
  return lambda(h): (2**degree * f(h/2) - f(h)) / (2**degree - 1)

def richardson(f):
  # TODO Memoize the incoming function (possibly with an explicit
  # stream) to save compute on repeated evaluations at the same h

  # Could also implement the "stop when at machine precision" rule,
  # instead of always taking exactly four steps.
  return richardson_step(richardson_step(richardson_step(richardson_step(f, 2), 4), 6), 8)(0.001)

def tweaking_lens(lens, thunk):
  def f(h):
    x = lens.get()
    try:
      lens.set(x + h)
      ans = thunk()
      return ans
    except VentureTypeError:
      # Interpret a Venture type error as a constraint violation
      # caused by taking the step.  This is useful because the
      # carefully function in the randomized testing framework
      # interprets value errors as a signal that it chose bad
      # arguments.
      # TODO Maybe rewrite richardson to do a one-sided limit if the
      # other side steps off the cliff?
      import sys
      info = sys.exc_info()
      raise ValueError(info[1]), None, info[2]
    finally:
      # Leave the value in the lens undisturbed
      lens.set(x)
  return f

def gradient_from_lenses(thunk, lenses):
  return [richardson(derivative(tweaking_lens(lens, thunk), 0)) for lens in lenses]
