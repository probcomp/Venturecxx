# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import subprocess as s
from nose import SkipTest
import requests as r
import pexpect
import sys

def available_containers():
  p = s.Popen(["docker", "ps"], stdout=s.PIPE)
  (out, _) = p.communicate()
  if p.returncode != 0:
    print out
    raise SkipTest("Failed to run docker command.  If it's a socket permission problem, make sure the 'docker' group exists, and the user running this test is a member of it; then run 'sudo service docker.io restart' and 'newgrp docker' and try again.")
  lines = out.splitlines()
  assert len(lines) > 0
  containers = [l.split() for l in lines[1:]]
  return containers

def test_docker_install():
  assert len(available_containers()) == 0

  assert s.call(["script/build_docker_image"]) == 0
  
  try:
    child = pexpect.spawn("script/run_docker_container")
    child.logfile = sys.stdout
    child.expect('root@.*:/root/Venturecxx# ')

    # Check that the supervisor is running
    req = r.get("http://localhost:9001")
    assert req.status_code == 200
    # Check that the supervisor thinks it's supervising the IPython
    # notebook server and the vnc server
    assert "ipython_notebook" in req.content
    assert "x11vnc" in req.content

    # Smoketest commandline venture in the container
    child.sendline("venture puma -e '[infer (bind (collect (normal 0 1)) printf)]'")
    child.expect(r"\(normal 0.0 1.0\)")
    child.expect('root@.*:/root/Venturecxx# ')
  finally:
    for c in available_containers():
      s.check_call(["docker", "stop", c[0]])

if __name__ == '__main__':
  test_docker_install()
