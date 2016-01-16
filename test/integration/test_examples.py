# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import contextlib
import copy
import os.path
import shutil
import sys
import subprocess as s
import tempfile
from unittest import SkipTest
from distutils.spawn import find_executable

from venture.test.config import gen_in_backend, gen_needs_backend, gen_needs_ggplot
from venture.test.config import in_backend, needs_backend

def findTimeout():
  '''
  Find the timeout shell command. If not present, skip the test.
  '''
  if find_executable('timeout'):
    return 'timeout'
  elif find_executable('gtimeout'):
    return 'gtimeout'
  else:
    errstr = '"timeout" command line executable not found; skipping.'
    raise SkipTest(errstr)

def checkVentureExample(command):
  timeout = findTimeout()
  assert s.call("%s 1.5s %s" % (timeout, command), shell=True) == 124

@gen_in_backend("none")
@gen_needs_backend("puma")
@gen_needs_ggplot
def testVentureExamplesPuma():
  for ex in ["venture puma -f examples/plotting/bimodal.vnt",
             "venture puma -f examples/plotting/dice_plot.vnt",
             "venture puma -f examples/plotting/normal_plot.vnt",
             "venture puma -f examples/trickiness-concrete.vnts",
             "venture puma -f examples/trickiness-concrete-2.vnts",
  ]:
    yield checkVentureExample, ex

@gen_in_backend("none")
@gen_needs_backend("lite")
@gen_needs_ggplot
def testVentureExamplesLitePlot():
  for ex in ["venture lite -f examples/trickiness-ideal.vnts",
  ]:
    yield checkVentureExample, ex

@gen_in_backend("none")
@gen_needs_backend("lite")
def testVentureExamplesLite():
  for ex in ["venture lite -L examples/hmm_plugin.py -f examples/hmm.vnt -e 'infer exact_filtering()'",
  ]:
    yield checkVentureExampleComplete, ex

def checkVentureExampleComplete(command):
  assert s.call(command, shell=True) == 0

@gen_in_backend("none")
@gen_needs_backend("puma")
def testVentureExamplesPumaComplete():
  lda_cmd = "'do(model(2, 2), data(3, 4), mh(default, one, 500))'"
  for ex in ["venture puma -f examples/crosscat.vnt -e smoke_test",
             "venture puma -f examples/lda.vnt -e " + lda_cmd  ]:
    yield checkVentureExampleComplete, ex

@contextlib.contextmanager
def extra_module_path(path):
  root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
  exs_path = os.path.join(root, path)
  old_path = copy.copy(sys.path)
  sys.path.append(exs_path)
  yield
  sys.path = old_path

@contextlib.contextmanager
def temp_directory(suffix):
  temp_dir = None
  try:
    temp_dir = tempfile.mkdtemp(suffix=suffix)
    yield temp_dir
  finally:
    if temp_dir is not None:
      shutil.rmtree(temp_dir)

@in_backend("none")
@needs_backend("lite")
def testGaussianGeweke():
  with extra_module_path("examples"):
    with temp_directory("geweke") as plots_dir:
      import gaussian_geweke
      gaussian_geweke.main(outdir=plots_dir, n_sample=2, burn_in=2, thin=2)

@in_backend("none")
@needs_backend("lite")
def testCrp2dDemo():
  with extra_module_path("examples"):
    import crp_2d_demo
    crp_2d_demo.doit(num_points=2, num_frames=3, show_pics=False)

@in_backend("none")
@needs_backend("lite")
def testHmcDemo():
  with extra_module_path("examples"):
    with temp_directory("hmc") as plot_dir:
      import hmc_demo
      hmc_demo.doit(nsamples=3, nruns=1, plot_dir=plot_dir, contour_delta=2)
