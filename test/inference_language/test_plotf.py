from os import remove
from os.path import exists
from nose.tools import assert_raises_regexp

from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim
from venture.exception import VentureException

@on_inf_prim("plotf_to_file")
def testPlotfToFile1():
  'Test that plotf_to_file dumps file of correct name'
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  res = ripl.infer('(cycle ((mh default one 10) (plotf_to_file test1 h0 x)) 10)')
  print res
  testfile = 'test1.png'
  assert exists(testfile)
  remove(testfile)

@on_inf_prim("plotf_to_file")
def testPlotfToFile2():
  'Test that plotf_to_file handles multiple files correctly'
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  res = ripl.infer('(cycle ((mh default one 10) (plotf_to_file (test1 test2) (h0 lcd0d) x)) 10)')
  print res
  testfiles = ['test1.png', 'test2.png']
  for testfile in testfiles:
    assert exists(testfile)
    remove(testfile)

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
  infer = '(cycle ((mh default one 10) (plotf_to_file {0} {1} x)) 10)'
  infer = infer.format(basenames, specs)
  with assert_raises_regexp(VentureException, 'evaluation: The number of specs must match the number of filenames.'):
    ripl.infer(infer)
