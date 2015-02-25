import subprocess as s
from unittest import SkipTest
from distutils.spawn import find_executable

from venture.test.config import gen_in_backend

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
def testExamples():
  for ex in ["venture-unit/lda.py", "venture-unit/crosscat.py", "venture-unit/analytics_gaussian_geweke.py",
             "venture-unit/crp-demo.py", "venture-unit/crp-2d-demo.py", "venture-unit/hmc-demo.py",
             "venture-unit/hmm-demo.py"]:
    yield checkExample, ex
