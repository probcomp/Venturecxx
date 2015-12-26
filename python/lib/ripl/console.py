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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cmd import Cmd
from functools import wraps
import copy
import os
import traceback

from venture.exception import VentureException
from venture.ripl.utils import strip_types

def printValue(directive):
  '''Gets the actual value returned by an assume, predict, report, or sample directive.'''
  if directive is None or 'value' not in directive:
    pass
  else:
    print strip_types(directive['value'])

def catchesVentureException(f):
  @wraps(f)
  def try_f(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except VentureException as e:
      print e
    except Exception:
      print "Your query has generated an error:"
      traceback.print_exc()
    except KeyboardInterrupt:
      pass

  return try_f

class RiplCmd(Cmd, object):
  def __init__(self, ripl, rebuild, files=None, plugins=None):
    super(RiplCmd, self).__init__()
    self.ripl = ripl
    self.prompt = 'venture[script] > '
    self.rebuild = rebuild
    self.files = [] if files is None else files
    self.plugins = [] if plugins is None else plugins
    self.pending_instruction_string = None
    self._update_prompt()

  @catchesVentureException
  def emptyline(self):
    if self.pending_instruction_string is not None:
      # force evaluation of pending instruction
      self._do_continue_instruction("", force_complete=True)

  def do_quit(self, _s):
    '''Exit the Venture console.'''
    print ''
    print "End of input reached."
    print "Moriturus te saluto."
    return True

  do_EOF = do_quit

  def _do_instruction(self, s, force_complete=False):
    if self.ripl.get_mode() == "church_prime":
      # Not supporting multiline paste for abstract syntax yet
      return self.ripl.execute_instructions(s)
    else:
      from venture.parser.venture_script.parse import string_complete_p
      if force_complete or string_complete_p(s):
        return self.ripl.execute_instructions(s)
      else:
        self.pending_instruction_string = s
        self._update_prompt()

  @catchesVentureException
  def postcmd(self, stop, line):
    callbacks = self.ripl.sivm.core_sivm.engine.callbacks
    if '__postcmd__' in callbacks:
      inferrer = self.ripl.evaluate('__the_inferrer__')
      callbacks['__postcmd__'](inferrer)
    return stop

  @catchesVentureException
  def default(self, line):
    '''Continue a pending instruction or evaluate an expression in the inference program.'''
    if self.pending_instruction_string is None:
      self._do_eval(line)
    else:
      self._do_continue_instruction(line)

  def _do_continue_instruction(self, line, force_complete=False):
    string = self.pending_instruction_string + "\n" + line
    self.pending_instruction_string = None
    self._update_prompt()
    printValue(self._do_instruction(string, force_complete))

  def _do_eval(self, line):
    '''Evaluate an expression in the inference program.'''
    printValue(self._do_instruction(line))

  @catchesVentureException
  def do_list_directives(self, _s):
    '''List active directives and their current values.'''
    self.ripl.print_directives()

  def do_get_directive(self, s):
    '''List active directives and their current values.'''
    # See whether we got a string representing an integer directive id
    try:
      s = int(s)
    except: pass
    self.ripl.print_one_directive(self.ripl.get_directive(s))

  @catchesVentureException
  def do_clear(self, _):
    '''Clear the console state.  (Replay the effects of command line arguments.)'''
    self.ripl.stop_continuous_inference()
    (_, self.ripl, files, plugins) = self.rebuild()
    self.files = files
    self.plugins = plugins
    self._update_prompt()

  @catchesVentureException
  def do_ci_status(self, _s):
    '''Report status of continuous inference.'''
    print self.ripl.continuous_inference_status()

  @catchesVentureException
  def do_dump_profile_data(self, s):
    '''Save the current profile data to the given file.'''
    self.ripl.profile_data().to_csv(s)
    print "Profile data saved to %s" % s

  @catchesVentureException
  def do_shell(self, s):
    '''Escape into the underlying shell.'''
    os.system(s)

  @catchesVentureException
  def do_load(self, s):
    '''Load the given Venture file.'''
    self.ripl.execute_program_from_file(s)
    self.files.append(s)
    self._update_prompt()

  @catchesVentureException
  def do_reload(self, _):
    '''Reload all previously loaded Venture files.'''
    plugins = copy.copy(self.plugins)
    files = copy.copy(self.files)
    self.do_clear(None)
    for p in plugins:
      if p not in self.plugins:
        self.do_load_plugin(p)
    for f in files:
      if f not in self.files:
        self.do_load(f)

  @catchesVentureException
  def do_load_plugin(self, s):
    '''Load the given plugin.'''
    # TODO Make a way to pass arguments to the plugin
    self.ripl.load_plugin(s)
    self.plugins.append(s)
    self._update_prompt()

  def _update_prompt(self):
    if self.pending_instruction_string is None:
      if len(self.files) == 0 and len(self.plugins) == 0:
        self.prompt = "venture[script] > "
      else:
        self.prompt = "venture[script] " + " ".join(self.plugins + self.files) + " > "
    else:
      self.prompt =   "            ... > "

def run_venture_console(ripl, rebuild, files=None, plugins=None):
  RiplCmd(ripl, rebuild, files=files, plugins=plugins).cmdloop()

def main():
  import venture.shortcuts as s
  def build():
    return s.make_puma_church_prime_ripl()
  run_venture_console(build(), build)

if __name__ == '__main__': main()
