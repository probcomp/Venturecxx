# Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

import os.path

import matplotlib.pyplot as plt
import numpy as np
import scipy

from venture.shortcuts import make_lite_church_prime_ripl

model = """
[assume x (tag 'param 0 (uniform_continuous -4 4))]
[assume y (tag 'param 0 (uniform_continuous -4 4))]
[assume xout
  (if (< x 0)
      (normal x 0.5)
      (normal x 4))]
[assume out
  (multivariate_normal
   (array xout y)
   (matrix (list (list 1 0.5) (list 0.5 1))))]
"""

observation = """
; Should be [observe out (list 0.0 0.0)], but we can't put evaluated
; expressions on the right-hand side of `observe' at the moment.
[infer (observe out (list 0.0 0.0))]
"""

examples = [
  ("hmc", "(hmc 'param all 0.1 20 1)"),
  ("mh", "(mh default one 10)"),
  ("grad_ascent", "(grad_ascent 'param all 0.1 2 1)"),
]

# int_R pdf(xout|x) pdf([0,0]|[xout, y])
def true_pdf(x, y):
  cov = np.matrix([[1, 0.5], [0.5, 1]])
  scale = 0.5 if x < 0 else 4
  import scipy.integrate as integrate
  from venture.lite.utils import logDensityMVNormal
  def postprop(xout):
    prior = scipy.stats.norm.pdf(xout, loc=x, scale=scale)
    likelihood = logDensityMVNormal([0,0], np.array([xout,y]), cov)
    # TODO Should this be math.exp(likelihood)?
    return prior * np.exp(likelihood)
  (ans,_) = integrate.quad(postprop, x-4*scale, x+4*scale)
  return ans

def compute(nsamples, program):
  ripl = make_lite_church_prime_ripl()
  ripl.execute_program(model)
  ripl.execute_program(observation)
  dataset = ripl.infer("""
    (let ((d (empty)))
      (do (repeat %s (do %s (bind (collect x y) (curry into d))))
          (return d)))
  """ % (nsamples, program))
  return dataset.asPandas()

def plot(name, xname, yname, style, dfs, contour_func=None, contour_delta=None,
    ax=None):
  if contour_delta is None:
    contour_delta = 0.125
  if ax is None:
    ax = plt.gca()
  ax.set_title(name)
  ax.set_xlabel(xname)
  ax.set_ylabel(yname)
  for label, df in dfs:
    ax.plot(df[xname], df[yname], style, label=label)
  xmin, xmax, xfuzz = bounds(dfs, xname)
  ymin, ymax, yfuzz = bounds(dfs, yname)
  ax.set_xlim([xmin, xmax])
  ax.set_ylim([ymin, ymax])
  ax.legend()
  if contour_func is not None:
    # Adding the fuzz again is a kludgey attempt to keep the contours
    # from being cut off.  It doesn't always work but it usually looks
    # marginally better, without incurring a terribly substantial
    # performance hit when the function being contoured does heavy
    # numerical integration.
    xc = np.arange(xmin - xfuzz, xmax + xfuzz, contour_delta)
    yc = np.arange(ymin - yfuzz, ymax + yfuzz, contour_delta)
    XG, YG = np.meshgrid(xc, yc)
    ZG = np.vectorize(contour_func)(XG, YG)
    ax.contour(XG, YG, ZG)

def bounds(dfs, var):
  minimum = min(v for _l, df in dfs for v in df[var])
  maximum = max(v for _l, df in dfs for v in df[var])
  fuzz = 0.1 * max(maximum - minimum, 1.)
  return minimum - fuzz, maximum + fuzz, fuzz

def doit(nsamples, nruns, plot_dir, contour_delta):
  overlay = [0] * len(examples) * nruns
  for i, (name, program) in enumerate(examples):
    datasets = [0] * nruns
    for run in xrange(nruns):
      ds_name = "%s %d" % (name, run)
      print ds_name
      datasets[run] = (ds_name, compute(nsamples, program))
      overlay[nruns*i + run] = datasets[run]
    plot(name, "x", "y", "-o", datasets, contour_func=true_pdf,
      contour_delta=contour_delta, ax=plt.figure().gca())
    if plot_dir is None:
      plt.show()
    else:
      plt.savefig(os.path.join(plot_dir, name + ".png"))
      plt.clf()
  plot("overlay", "x", "y", "o", overlay, contour_func=true_pdf,
    contour_delta=contour_delta, ax=plt.figure().gca())
  if plot_dir is None:
    plt.show()
  else:
    plt.savefig(os.path.join(plot_dir, "all.png"))
    plt.clf()

if __name__ == "__main__":
  doit(nsamples=70, nruns=3, plot_dir=None, contour_delta=0.5)
