import subprocess as s

def testSPDocAutogens():
  dev_null = open("/dev/null", "w")
  assert s.call(["script/list-sps"], stdout=dev_null) == 0
