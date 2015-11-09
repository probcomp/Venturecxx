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

import subprocess as s
from unittest import SkipTest
from distutils.spawn import find_executable

from venture.test.config import gen_in_backend, gen_needs_backend, gen_needs_ggplot

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

def checkExample(example):
  timeout = findTimeout()
  assert s.call("%s 1.5s python examples/%s" % (timeout, example), shell=True) == 124

@gen_in_backend("none")
@gen_needs_backend("puma")
def testExamplesPuma():
  for ex in ["venture-unit/lda.py", "venture-unit/crosscat.py"]:
    yield checkExample, ex

@gen_in_backend("none")
@gen_needs_backend("lite")
def testExamples():
  for ex in ["venture-unit/crp-demo.py", "venture-unit/crp-2d-demo.py", "venture-unit/hmc-demo.py",
             "venture-unit/hmm-demo.py"]:
    yield checkExample, ex

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
    yield checkVentureExample, ex
