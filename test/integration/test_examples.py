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

import contextlib
import copy
import os.path
import shutil
import subprocess as s
import sys
import tempfile

from venture.test.config import gen_in_backend
from venture.test.config import gen_needs_backend
from venture.test.config import gen_needs_ggplot
from venture.test.config import in_backend
from venture.test.config import needs_backend

def checkVentureExample(command):
  assert s.call(command, shell=True) == 0

@gen_in_backend("none")
@gen_needs_backend("lite")
def testVentureExamplesLite():
  for ex in ["venture lite -L examples/hmm_plugin.py -f examples/hmm.vnt -e 'infer exact_filtering()'",
  ]:
    yield checkVentureExample, ex

@gen_in_backend("none")
@gen_needs_backend("puma")
def testVentureExamplesPumaComplete():
  lda_cmd = "'do(model(2, 2), data(3, 4), mh(default, one, 500))'"
  for ex in ["venture puma -f examples/crosscat.vnt -e smoke_test",
             "venture puma -f examples/lda.vnt -e " + lda_cmd,
             "cd examples/ppaml-talk && venture puma -f pipits.vnts -e 'do_sweeps(5)'",
  ]:
    yield checkVentureExample, ex

@contextlib.contextmanager
def temp_directory(suffix):
  temp_dir = None
  try:
    temp_dir = tempfile.mkdtemp(suffix=suffix)
    yield temp_dir
  finally:
    if temp_dir is not None:
      shutil.rmtree(temp_dir)

def checkVentureExampleRude(command):
  with temp_directory("plotpen") as plotpen:
    assert s.call(command, cwd=plotpen, shell=True) == 0

@gen_in_backend("none")
@gen_needs_backend("lite")
@gen_needs_ggplot
def testVentureExamplesLitePlot():
  my_dir = os.path.abspath(os.path.dirname(__file__))
  for ex in ["venture lite -f %s/../../examples/trickiness-ideal.vnts" % (my_dir,),
  ]:
    yield checkVentureExampleRude, ex

@gen_in_backend("none")
@gen_needs_backend("puma")
@gen_needs_ggplot
def testVentureExamplesPumaPlot():
  my_dir = os.path.abspath(os.path.dirname(__file__))
  root = os.path.dirname(os.path.dirname(my_dir))
  for ex in [
    "venture puma -f %s/examples/plotting/bimodal.vnt" % (root,),
    "venture puma -f %s/examples/plotting/dice_plot.vnt" % (root,),
    "venture puma -f %s/examples/plotting/normal_plot.vnt" % (root,),
    "venture puma -f %s/examples/trickiness-concrete.vnts" % (root,),
    "venture puma -f %s/examples/trickiness-concrete-2.vnts" % (root,),
  ]:
    yield checkVentureExampleRude, ex

@contextlib.contextmanager
def extra_module_path(path):
  root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
  exs_path = os.path.join(root, path)
  old_path = copy.copy(sys.path)
  sys.path.append(exs_path)
  yield
  sys.path = old_path

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
      hmc_demo.doit(nsamples=3, nruns=1, plot_dir=plot_dir, contour_res=2)
