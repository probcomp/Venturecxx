import os
from subprocess import *

def testConsoleAlive():
  console = Popen("venture", shell=True, stdout=PIPE, stdin=PIPE)
  (stdout, _) = console.communicate("assume x (uniform_continuous 0.0 0.9)")
  assert console.returncode == 0
  assert '>>> 0.' in stdout
  print stdout
