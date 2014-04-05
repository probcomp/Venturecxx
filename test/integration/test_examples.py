import subprocess as s

def checkExample(example):
  assert s.call("timeout 1.5s python examples/%s" % example, shell=True) == 124

def testExamples():
  for ex in ["lda.py", "crosscat.py"]:
    yield checkExample, ex
