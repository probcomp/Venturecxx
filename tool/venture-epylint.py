#!/usr/bin/env python

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

# From the Internet (specifically, a pastebin referenced from
# http://www.emacswiki.org/emacs/PythonProgrammingInEmacs)

# The goal of this script is to reformat the messages emitted by
# Pylint into a form that Emacs' Flymake mode will understand, while
# respecting the Venture pylint configuration file.

import os.path
import re
import sys

from subprocess import Popen, PIPE

ignore = ",".join ( [
    "C0103",  # Naming convention
    "I0011",  # Warning locally suppressed using disable-msg
    "I0012",  # Warning locally suppressed using disable-msg
    "W0511",  # FIXME/TODO
    "W0142",  # *args or **kwargs magic.
    "R0904",  # Too many public methods
    "R0201",  # Method could be a function
] )

mypath = os.path.dirname(os.path.realpath(sys.argv[0]))
lintfile = mypath + "/pylintrc"

workdir = os.path.dirname(sys.argv[1])
filename = os.path.basename(sys.argv[1])

cmd = "pylint --output-format parseable --reports n --rcfile %s %s" % \
    (lintfile, filename)

p = Popen ( cmd, shell = True, bufsize = -1, cwd = workdir or None,
            stdin = PIPE, stdout = PIPE, close_fds = True )
pylint_re = re.compile (
    '^([^:]+):(\d+):\s*\[([WECR])([^,]+),\s*([^\]]+)\]\s*(.*)$'
    )
pylint_no_context_re = re.compile (
    '^([^:]+):(\d+):\s*\[([WECR])([^,]+)\]\s*(.*)$'
    )

for line in p.stdout:
    line = line.strip()
    matched = False
    m = pylint_re.match(line)
    if m:
        filename, linenum, errtype, errnum, context, description = m.groups()
        matched = True
    m = pylint_no_context_re.match(line)
    if m:
        filename, linenum, errtype, errnum, description = m.groups()
        matched = True
    if matched:
        if errtype == "E":
            msg = "Error"
        else:
            msg = "Warning"
        # Here we are targetting the following flymake regexp:
        #
        #  ("\\(.*\\) at \\([^ \n]+\\) line \\([0-9]+\\)[,.\n]" 2 3 nil 1)
        #
        # where the number at the end indicate the index into the regexp
        # groups of ( file, line, column, error text )
        #
        # You can see what regexps flymake uses to parse its output by   
        # running 'M-x describe-variable' on the variable
        # 'flymake-err-line-patterns'
    
        print "%s %s%s %s at %s line %s." % ( msg, errtype, errnum,
                                                  description, filename, linenum )
