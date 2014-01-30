#!/usr/bin/env python

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

cmd = "pylint --output-format parseable --include-ids y --reports n --rcfile %s %s" % \
    (lintfile, filename)

p = Popen ( cmd, shell = True, bufsize = -1, cwd = workdir,
            stdin = PIPE, stdout = PIPE, stderr = PIPE, close_fds = True )
pylint_re = re.compile (
    '^([^:]+):(\d+):\s*\[([WECR])([^,]+),\s*([^\]]+)\]\s*(.*)$'
    )
for line in p.stdout:
    line = line.strip()
    m = pylint_re.match ( line )
    if m:
        filename, linenum, errtype, errnum, context, description = m.groups()
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
