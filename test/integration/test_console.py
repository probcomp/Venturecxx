"""Integration tests for python/ripl/console.py and related.

Test that things we expect to work at the console actually do.
"""
# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

import subprocess
from flaky import flaky

from venture.test.config import in_backend

@in_backend("none")
def test_console_alive():
  console = subprocess.Popen("venture", shell=True,
                             stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  (stdout, _) = console.communicate("assume x = uniform_continuous(0.0, 0.9)")
  assert console.returncode == 0
  assert 'venture[script] > 0.' in stdout

@in_backend("none")
def test_console_multiline():
  console = subprocess.Popen("venture", shell=True,
                             stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  (stdout, _) = console.communicate(
      "assume x = \nuniform_continuous(0.0, 0.9)\n")
  assert console.returncode == 0
  assert '... > 0.' in stdout

import os
import pexpect
import re
import tempfile

TIMEOUT = 1
ROOT = os.path.dirname(os.path.abspath(__file__))

class SpawnVentureExpect(pexpect.spawn):
  """Wrap pexpect with prompts and expectations useful to Venture."""
  # https://pexpect.readthedocs.org/en/latest/overview.html
  def __init__(self, *args, **kwargs):
    if 'timeout' not in kwargs:
      kwargs['timeout'] = TIMEOUT
    self.ps1 = r'venture\[script\]( [^>]*)* > '  # regular prompt
    self.ps2 = r'^\s*\.\.\. >\s+'       # continuation prompt
    super(SpawnVentureExpect, self).__init__(*args, **kwargs)

  def send_command(self, cmd):
    """Sends the command and expects (skips) the corresponding output."""
    # As opposed to inherited send or sendline which leave you to do that.
    # Note: sendline is problematic because you don't know what the
    # line break is.
    cmd = cmd.strip()
    self.sendline(cmd)
    check_echo = ''
    for _ in xrange(len(re.split(r'[\r\n]+', cmd))):
      self.expect_exact('\r\n')
      check_echo += re.sub(self.ps1, '', re.sub(self.ps2, '', self.before))

    # Kludge to skip pty-introduced control characters on line
    # wraps which vary from system to system (e.g., Mac OS X
    # inserts SPC BS at end of line, whereas Linux inserts SPC CR).
    def remove_control(strn):
      return strn.translate(None, ''.join(map(chr, range(32 + 1) + [127])))
    # Turns out removing control characters is not enough to get
    # equality, because if the prompt and the command together are too
    # long, the pty might echo part of it
    assert remove_control(check_echo).endswith(remove_control(cmd))

  def expect_lines(self, lines):
    for line in lines:
      self.expect_exact(line + '\r\n')
      assert self.before == ''

  def read_to_prompt(self):
    self.expect(self.ps1)
    return self.before.strip()

  def expect_prompt(self):
    self.read_to_prompt()
    assert self.before == ''

  def expect_eof(self):
    self.expect(pexpect.EOF)

  def expect_timeout(self):
    self.expect(pexpect.TIMEOUT)

  def expect_capture(self, pattern):
    self.expect(pattern)
    if hasattr(self.match, 'groups'):
      return getattr(self.match, 'groups')()
    else:
      return None

  def expect_capture_one_int(self):
    groups = self.expect_capture(r'(-?\d+)')
    int_result = 0
    try:
      int_result = int(groups[0])
    except TypeError:
      assert False, self
    return int_result

  def expect_capture_one_intln(self):
    groups = self.expect_capture(r'(-?\d+)\r\n')
    int_result = 0
    try:
      int_result = int(groups[0])
    except TypeError:
      assert False, self
    return int_result

  def expect_capture_one_float(self):
    groups = self.expect_capture(r'(-?\d+\.\d+)')
    float_result = 0
    try:
      float_result = float(groups[0])
    except TypeError:
      assert False, self
    return float_result

  def expect_capture_one_floatln(self):
    groups = self.expect_capture(r'(-?\d+\.\d+)\r\n')
    float_result = 0
    try:
      float_result = float(groups[0])
    except TypeError:
      assert False, self
    return float_result


def spawn_venture(**kwargs):
  child = SpawnVentureExpect('venture', **kwargs)
  child.delaybeforesend = 0
  child.expect(r'\w+ backend', timeout=10)  # Startup time can be long.
  child.expect(
      r'Venture Script, version \S+\s+http://probcomp.csail.mit.edu/\S+',
      timeout=10)
  child.read_to_prompt()
  return child

# Tests begin
# ````````````````````````````````````````````````````````````````````````````
@in_backend("none")
def test_shell_loads():
  vnt = spawn_venture()
  assert vnt is not None

@in_backend("none")
def test_syntax_error():  # does not crash
  vnt = spawn_venture()
  vnt.send_command('c++')
  vnt.expect('Syntax error')
  vnt.read_to_prompt()

@in_backend("none")
def test_arithmetic():
  vnt = spawn_venture()
  # https://github.com/mit-probabilistic-computing-project/Venturecxx/issues/122
  for nine in ('9', '+9', '9.0',
               # '-(-9)', '--9',  *** text_parse: Syntax error at '-' (token 54)
               '0--9', '0 - -9',
               # '3+6', '3 +6',   *** text_parse: Syntax error at 6 (token 33)
               '3+ 6', '3 + 6', '3  +  6',
               # '10-1',          *** text_parse: Syntax error at -1 (token 33)
               '10 - 1', '10 + -1', '10+-1', '+10+-1', '+10-+1', '10-+1',
               '+3 + 6', '3 + +6', '+3 + +6', '+3+ +6', '+3 ++6', '+3++6',
               '81/9', '-27/-3'):
    vnt.send_command(nine)
    assert '9.0' == vnt.read_to_prompt(), nine

@in_backend("none")
def test_lines_and_comments():
  vnt = spawn_venture()

  vnt.send('\n')
  assert "" == vnt.read_to_prompt(), str(vnt)
  vnt.send_command('// just a comment by itself')
  assert "" == vnt.read_to_prompt(), str(vnt)

  def good(val):
    assert val >= 0.1, str(vnt)
    assert val <= 0.9, str(vnt)
    vnt.read_to_prompt()

  vnt.send_command('assume w = uniform_continuous(0.1, 0.9)')
  good(vnt.expect_capture_one_float())
  vnt.send_command("""assume x =
  uniform_continuous(0.1,
                     0.9)
  """)
  good(vnt.expect_capture_one_float())
  vnt.send_command("""assume y =
  //comment before
  uniform_continuous(0.1,  // comment two
                     // another comment.
                     0.9)
  """)
  good(vnt.expect_capture_one_float())
  vnt.send_command("""assume z =
  //comment before
  uniform_continuous(0.1,  // comment two
                     // another comment.
                     0.9) //  Comment after.
  """)
  good(vnt.expect_capture_one_float())
  # Bug in console.py:precmd: it should handle multiline but doesn't?
  # *** text_parse: Syntax error at 'bad' (token 2)
  # vnt.send_command("""(assume bad =
  # //comment before
  # uniform_continuous(0.1,  // comment two
  #                    // another comment.
  #                    0.9)
  #                    //  Comment after.
  #                    )
  # """)
  # good(vnt.expect_capture_one_floatln())

def test_eof_quits():
  vnt = spawn_venture()
  vnt.sendeof()
  vnt.expect("Moriturus te saluto")
  vnt.expect_eof()

def test_directives_and_forget():
  vnt = spawn_venture()

  vnt.send_command('assume x = normal(0, 1)')
  x_val = vnt.expect_capture_one_floatln()
  vnt.read_to_prompt()
  vnt.send_command('assume y = uniform_continuous(1, 2)')
  y_val = vnt.expect_capture_one_floatln()
  vnt.read_to_prompt()
  vnt.send_command('list_directives')
  x_id = vnt.expect_capture_one_int()
  vnt.expect_exact(': assume x = normal(0, 1):')
  x_val2 = vnt.expect_capture_one_floatln()
  y_id = vnt.expect_capture_one_int()
  vnt.expect_exact(': assume y = uniform_continuous(1, 2):')
  y_val2 = vnt.expect_capture_one_floatln()
  vnt.read_to_prompt()
  assert x_id > 0
  assert y_id > 0
  assert abs(x_val2 - x_val) < 10e-5
  assert abs(y_val2 - y_val) < 10e-5
  vnt.send_command('forget %d' % x_id)
  vnt.read_to_prompt()
  vnt.send_command('list_directives')
  next_y_id = vnt.expect_capture_one_int()
  next_y_val = vnt.expect_capture_one_floatln()
  assert next_y_id == y_id
  assert next_y_val == y_val
  vnt.read_to_prompt()
  vnt.send_command('clear')
  vnt.read_to_prompt()
  vnt.send_command('list_directives')
  vnt.read_to_prompt()
  assert "" == vnt.before

def test_python_eval():
  # https://github.com/mit-probabilistic-computing-project/Venturecxx/issues/122
  vnt = spawn_venture()
  vnt.send_command('pyexec("import collections")')
  assert "[]" == vnt.read_to_prompt()
  vnt.send_command('pyexec("d = collections.defaultdict(int)")')
  assert "[]" == vnt.read_to_prompt()
  vnt.send_command('pyexec("d[\\"a\\"]+=1")')
  assert "[]" == vnt.read_to_prompt()
  vnt.send_command('pyeval("d[\\"a\\"]")')
  assert 1 == vnt.expect_capture_one_intln()
  vnt.send_command('pyexec("d[\\"a\\"]+=1")')
  assert "[]" == vnt.read_to_prompt()
  vnt.send_command('pyeval("d[\\"a\\"]")')
  assert 2 == vnt.expect_capture_one_intln()

def test_shell():
  vnt = spawn_venture()
  vnt.send_command('shell echo foo')
  vnt.expect_exact('foo\r\n')
  # The shell console command is confusingly unlike pyexec, and just interprets
  # the rest of the line, so this is as if you had typed ("echo foo") at the
  # shell.
  vnt.send_command('shell("echo foo")')
  vnt.expect('not found')

def test_loading():
  vnt = spawn_venture()
  fvnts = tempfile.NamedTemporaryFile(suffix="play.vnts", delete=False)
  fvnts.write('print("I am a venture script")\n')
  fvnts.close()
  fplgn = tempfile.NamedTemporaryFile(suffix="play_plugin.py", delete=False)
  fplgn.write("""print "I am a plugin at load time"

def __venture_start__(*args, **kwargs):
    print "I am a plugin at start time " + repr(args) + repr(kwargs)
""")
  fplgn.close()
  vnts = os.path.abspath(fvnts.name)
  plgn = os.path.abspath(fplgn.name)
  vnt.send_command("load %s" % vnts)
  vnt.expect_exact("Strng(I am a venture script)\r\n")
  vnt.expect_prompt()
  vnt.send_command("load_plugin %s" % plgn)
  vnt.expect_exact("I am a plugin at load time\r\n")
  # Note: must end expect after unmatched open paren or the expectation fails.
  vnt.expect_exact("I am a plugin at start time (")
  vnt.expect_exact("venture.ripl.ripl.Ripl instance at 0x")
  vnt.expect(r"\w+")
  vnt.expect_exact(">,){}\r\n")
  vnt.expect_prompt()
  vnt.send_command("reload")
  vnt.expect_exact("I am a plugin at load time\r\n")
  vnt.expect_exact("I am a plugin at start time (")
  vnt.expect_exact("venture.ripl.ripl.Ripl instance at 0x")
  vnt.expect(r"\w+")
  vnt.expect_exact(">,){}\r\n")
  vnt.expect_exact("Strng(I am a venture script)\r\n")
  vnt.expect_prompt()
  vnt.send_command("clear")
  assert "" == vnt.read_to_prompt()
  # Now in the other order:
  vnt.send_command("load_plugin %s" % plgn)
  vnt.expect_exact("I am a plugin at load time\r\n")
  vnt.expect_exact("I am a plugin at start time (")
  vnt.expect_exact("venture.ripl.ripl.Ripl instance at 0x")
  vnt.expect(r"\w+")
  vnt.expect_exact(">,){}\r\n")
  vnt.expect_prompt()
  vnt.send_command("load %s" % vnts)
  vnt.expect_exact("Strng(I am a venture script)\r\n")
  vnt.expect_prompt()
  vnt.send_command("reload")
  vnt.expect_exact("I am a plugin at load time\r\n")
  vnt.expect_exact("I am a plugin at start time (")
  vnt.expect_exact("venture.ripl.ripl.Ripl instance at 0x")
  vnt.expect(r"\w+")
  vnt.expect_exact(">,){}\r\n")
  vnt.expect_exact("Strng(I am a venture script)\r\n")
  vnt.expect_prompt()
  vnt.send_command("clear")
  assert "" == vnt.read_to_prompt()
  vnt.send_command("reload")  # No longer have anything to reload.
  assert "" == vnt.read_to_prompt()
  os.unlink(vnts)
  os.unlink(plgn)

@flaky
def test_plots_to_file():
  vnt = spawn_venture(timeout=3)
  plotfile = tempfile.NamedTemporaryFile(suffix="plot.png", delete=False)
  plotpath = os.path.abspath(plotfile.name)
  vnt.send_command("assume x = normal(0, 1)")
  vnt.send_command("assume y = normal(x, 1)")
  vnt.send_command("observe y = 4")
  vnt.send_command("define chain_history = run(accumulate_dataset(50, \n" +
                   "do(default_markov_chain(1), collect(x))))")
  vnt.send_command('plot_to_file("%s", "lc0", chain_history)' % plotpath[0:-4])
  vnt.expect_exact("[]\r\n")
  vnt.send_command('shell file %s' % plotpath)
  vnt.expect_exact(plotpath)
  vnt.expect(r': PNG image data, \d\d+ x \d\d+, \d-bit.*\r\n')
