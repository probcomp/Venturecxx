from subprocess import *
import time

def checkExample(example):
  assert call("timeout 1.5s python examples/%s" % example, shell=True) == 124

def testExamples():
  for ex in ["lda.py", "crosscat.py"]:
    yield checkExample, ex
