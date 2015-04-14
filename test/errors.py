# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from nose.tools import assert_raises
from StringIO import StringIO
import sys
import re

from venture.exception import VentureException

ansi_escape = re.compile(r'\x1b[^m]*m')

def assert_sivm_annotation_succeeds(f, *args, **kwargs):
  with assert_raises(VentureException) as cm:
    f(*args, **kwargs)
  assert "stack_trace" in cm.exception.data

def assert_ripl_annotation_succeeds(f, *args, **kwargs):
  with assert_raises(VentureException) as cm:
    f(*args, **kwargs)
  assert hasattr(cm.exception, 'annotated') and cm.exception.annotated
  assert "stack_trace" in cm.exception.data

def assert_error_message_contains(text, f, *args, **kwargs):
  text = text.strip()
  with assert_raises(VentureException) as cm:
    f(*args, **kwargs)
  message = ansi_escape.sub('', str(cm.exception))
  if text in message:
    pass # OK
  else:
    print "Did not find pattern"
    print text
    print "in"
    import traceback
    print traceback.format_exc()
    print cm.exception
    assert text in message

def assert_print_output_contains(text, f, *args, **kwargs):
  text = text.strip()
  old_stderr = sys.stderr
  result = StringIO()
  sys.stderr = result
  f(*args, **kwargs)
  sys.stderr = old_stderr
  ans = result.getvalue()
  assert text in ansi_escape.sub('', ans)
