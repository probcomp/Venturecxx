from os import remove
from os.path import exists
from nose import SkipTest
from nose.tools import assert_raises_regexp

from venture.test.config import (get_ripl, on_inf_prim, gen_on_inf_prim,
                                 needs_ggplot, gen_needs_ggplot)
from venture.exception import VentureException

@needs_ggplot
@on_inf_prim("plotf_to_file")
def testPlotfToFile1():
  'Test that plotf_to_file dumps file of correct name'
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  prog = """
(let ((d (empty)))
  (do (cycle ((mh default one 10)
              (bind (collect x) (curry into d))) 10)
      (plotf_to_file (quote test1) (quote h0) d)))"""
  ripl.infer(prog)
  testfile = 'test1.png'
  assert exists(testfile)
  remove(testfile)

@needs_ggplot
@on_inf_prim("plotf_to_file")
def testPlotfToFile2():
  'Test that plotf_to_file handles multiple files correctly'
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  prog = """
(let ((d (empty)))
  (do (cycle ((mh default one 10)
              (bind (collect x) (curry into d))) 10)
      (plotf_to_file (quote (test1 test2)) (quote (h0 lcd0d)) d)))"""
  ripl.infer(prog)
  testfiles = ['test1.png', 'test2.png']
  for testfile in testfiles:
    assert exists(testfile)
    remove(testfile)

@gen_needs_ggplot
@gen_on_inf_prim("plotf_to_file")
def testPlotfToFileBadArgs():
  'Test that an error occurs if the number of basenames != the number of plot specs'
  for basenames, specs in [('test1', '(h0 lcd0d)'),
                           ('(test1 test2)', 'h0'),
                           ('(test1 test2 test3)', '(h0 lcd0d)')]:
    yield checkPlotfToFileBadArgs, basenames, specs

def checkPlotfToFileBadArgs(basenames, specs):
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  infer = """
(let ((d (empty)))
  (do (cycle ((mh default one 10)
              (bind (collect x) (curry into d))) 10)
      (plotf_to_file (quote {0}) (quote {1}) d)))"""
  infer = infer.format(basenames, specs)
  with assert_raises_regexp(VentureException, 'evaluation: The number of specs must match the number of filenames.'):
    ripl.infer(infer)
