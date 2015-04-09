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

import re
import os.path
import sys

# Using a class so that I can have local state.  Stupid broken Python
# closures.
class CodeBlocksInReadme(object):
  def __init__(self):
    self.blocks = []
    self.block_open = False
    self.maybes_tail = []

  def in_block(self, line):
    if not self.block_open:
      self.block_open = True
      self.blocks.append([])
    self.blocks[-1].extend(self.maybes_tail)
    self.maybes_tail = []
    self.blocks[-1].append(line)

  def not_in_block(self):
    self.block_open = False
    self.maybes_tail = []

  def maybe_in_block(self, line):
    if self.block_open:
      self.maybes_tail.append(line)

  def __call__(self):
    with open(os.path.dirname(__file__) + "/../../README.md") as f:
      for line in f:
        if re.match(r"    .+", line):
          self.in_block(line[4:])
        elif re.match(r".+", line):
          self.not_in_block()
        else:
          self.maybe_in_block(line)
    return ["".join(b) for b in self.blocks]

def code_blocks_in_readme():
  return CodeBlocksInReadme()()

def code_of_script(name):
  with open(os.path.dirname(__file__) + "/../../script/" + name) as f:
    return f.read()

def check_readme_agrees_with_script(name):
  target = code_of_script(name)
  for block in code_blocks_in_readme():
    if "#!/bin/bash -xe\n\n" + block == target:
      return # Success.

  # Failure; produce a nice explanation of it.
  for block in code_blocks_in_readme():
    sys.stdout.write(block)
    print "-----"
  sys.stdout.write(target)

  assert False, "None of the code blocks in the README (repeated above) look like the %s script (also repeated above)." % name

def test_readme_agreements():
  yield check_readme_agrees_with_script, "provision_ubuntu_dependencies"
  yield check_readme_agrees_with_script, "prepare_virtualenv"
