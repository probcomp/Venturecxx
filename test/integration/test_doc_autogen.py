import subprocess as s

def testSPDocAutogens():
  assert s.call(["script/list-sps"]) == 0
