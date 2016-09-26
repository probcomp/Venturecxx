# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from os import remove
from os.path import exists

from nose.tools import assert_raises_regexp

from venture.exception import VentureException
from venture.test.config import capture_output
from venture.test.config import gen_needs_ggplot
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import needs_ggplot
from venture.test.config import on_inf_prim

@needs_ggplot
@on_inf_prim("plotf_to_file")
def testPlotfToFile1():
  # Test that plotf_to_file dumps file of correct name
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  testfile = 'test1.png'
  prog = """
(let ((d (empty)))
  (do (repeat 10
       (do (mh default one 10)
           (bind (collect x) (curry into d))))
      (plotf_to_file (quote test1) (quote h0) d)))"""
  try:
    ripl.infer(prog)
    assert exists(testfile)
  finally:
    if exists(testfile):
      remove(testfile)

@needs_ggplot
@on_inf_prim("plotf_to_file")
def testPlotToFile1():
  # Test that plot_to_file dumps file of correct name
  # TODO Delete this duplicate test if plotf becomes an alias for return plot
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  testfile = 'test1.png'
  prog = """
[define d (empty)]
[infer
  (do (repeat 10
       (do (mh default one 10)
           (bind (collect x) (curry into d)))))]
(plot_to_file (quote test1) (quote h0) d)"""
  try:
    ripl.execute_program(prog)
    assert exists(testfile)
  finally:
    if exists(testfile):
      remove(testfile)

@needs_ggplot
@on_inf_prim("plotf_to_file")
def testPlotfToFile2():
  # Test that plotf_to_file handles multiple files correctly
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  testfiles = ['test1.png', 'test2.png']
  prog = """
(let ((d (empty)))
  (do (repeat 10
       (do (mh default one 10)
           (bind (collect x) (curry into d))))
      (plotf_to_file (quote (test1 test2)) (quote (h0 lcd0d)) d)))"""
  try:
    ripl.infer(prog)
    for testfile in testfiles:
      assert exists(testfile)
  finally:
    for testfile in testfiles:
      if exists(testfile):
        remove(testfile)

@gen_needs_ggplot
@gen_on_inf_prim("plotf_to_file")
def testPlotfToFileBadArgs():
  # Test that an error occurs if the number of basenames != the number
  # of plot specs
  for basenames, specs in [('test1', '(h0 lcd0d)'),
                           ('(test1 test2)', 'h0'),
                           ('(test1 test2 test3)', '(h0 lcd0d)')]:
    yield checkPlotfToFileBadArgs, basenames, specs

def checkPlotfToFileBadArgs(basenames, specs):
  # Enable the persistent_inference_trace in order to trigger the
  # inference prelude entry skipping hack in error annotation
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.assume('x', '(normal 0 1)')
  infer = """
(let ((d (empty)))
  (do (repeat 10
       (do (mh default one 10)
           (bind (collect x) (curry into d))))
      (plotf_to_file (quote {0}) (quote {1}) d)))"""
  infer = infer.format(basenames, specs)
  with assert_raises_regexp(VentureException, 'evaluation: The number of specs must match the number of filenames.') as cm:
    ripl.infer(infer)
  assert "stack_trace" in cm.exception.data # I.e., error annotation succeeded.

@on_inf_prim("collect")
def testIteration():
  # Check that the iteration counter prints correctly
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  program = """[infer
(let ((d (empty)))
  (repeat 5
   (do (mh default one 10)
       (bind (collect x) (curry into d))
       (sweep d))))]"""
  res, captured = capture_output(ripl, program)
  assert captured == '\n'.join(['Iteration count: ' + str(x) for x in range(1,6)]) + '\n'
