# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

from venture.test.config import in_backend

@in_backend("none")
def testConsoleAlive():
  console = s.Popen("venture", shell=True, stdout=s.PIPE, stdin=s.PIPE)
  (stdout, _) = console.communicate("assume x = uniform_continuous(0.0, 0.9)")
  assert console.returncode == 0
  assert 'venture[script] > 0.' in stdout
  print stdout

@in_backend("none")
def testConsoleMultiline():
  console = s.Popen("venture", shell=True, stdout=s.PIPE, stdin=s.PIPE)
  (stdout, _) = console.communicate("assume x = \nuniform_continuous(0.0, 0.9)\n")
  assert console.returncode == 0
  assert '... > 0.' in stdout
  print stdout
