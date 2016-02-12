#!/usr/bin/env python

# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

"""Write a requirements file specifying the minimum declared versions of Venture's dependencies (for testing)."""

import os

import pkg_resources as pkg

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_req_file(filename):
    def parse_req_line(line):
        return line.split('#')[0].strip()
    return [parse_req_line(line)
            for line in open(filename).read().splitlines()
            if len(parse_req_line(line)) > 0]

install_requires = parse_req_file(os.path.join(root, "install_requires.txt"))

def all_versions(name):
    cmd = "curl -s https://pypi.python.org/pypi/%s/json | jq -r '.releases | keys | .[]'" % (name,)
    candidates = os.popen(cmd).read().splitlines()
    return sorted(candidates, key=pkg.parse_version)

def valid_versions(requirement):
    candidates = all_versions(requirement.project_name)
    return [c for c in candidates if c in requirement]

# All valid versions of all listed dependencies
# for req in pkg.parse_requirements(install_requires):
#     print req.project_name
#     print valid_versions(req)

for req in pkg.parse_requirements(install_requires):
    print "%s==%s" % (req.project_name, valid_versions(req)[0])
