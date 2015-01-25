import subprocess as s

from venture.test.config import in_backend

@in_backend("none")
def testSPDocAutogens():
  dev_null = open("/dev/null", "w")
  assert s.call(["vendoc"], stdout=dev_null) == 0
