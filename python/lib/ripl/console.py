# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
from cmd import Cmd
from venture.exception import VentureException
from utils import _strip_types, expToDict, parse
from functools import wraps

def getValue(directive):
  '''Gets the actual value returned by an assume, predict, report, or sample directive.'''
  return _strip_types(directive['value'])

def catchesVentureException(f):
  @wraps(f)
  def try_f(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except VentureException as e:
      print e
      if e.exception in ['parse', 'text_parse', 'invalid_argument']:
        print e.data['instruction_string']
        offset = e.data['text_index'][0]
        length = e.data['text_index'][1] - offset + 1
        underline = ''.join([' '] * offset + ['^'] * length)
        print underline
    except Exception:
      print "Your query has generated an error:"
      traceback.print_exc()

  return try_f

class RiplCmd(Cmd, object):
  def __init__(self, ripl):
    super(RiplCmd, self).__init__()
    self.ripl = ripl
    self.prompt = '>>> '

  def emptyline(self):
    pass

  def do_quit(self, _s):
    '''Exit the Venture console.'''
    print ''
    print "End of input reached."
    print "Moriturus te saluto."
    return True

  do_EOF = do_quit

  def _do_instruction(self, instruction, s):
    return self.ripl.execute_instruction('[%s %s]' % (instruction, s))

  def precmd(self, line):
    line = line.strip()
    if len(line) > 0 and (line[0] == "[" or line[0] == "("):
      if line[-1] == "]" or line[-1] == ")":
        return line[1:-1]
    return line

  @catchesVentureException
  def do_assume(self, s):
    '''Add a named variable to the model.'''
    print getValue(self._do_instruction('assume', s))

  @catchesVentureException
  def do_observe(self, s):
    '''Condition on an expression being the value.'''
    self._do_instruction('observe', s)

  @catchesVentureException
  def do_predict(self, s):
    '''Register an expression as a model prediction.'''
    print getValue(self._do_instruction('predict', s))

  @catchesVentureException
  def do_forget(self, s):
    '''Forget a given prediction or observation.'''
    self._do_instruction('forget', s)

  @catchesVentureException
  def do_report(self, s):
    '''Report the current value of a given directive.'''
    print getValue(self._do_instruction('report', s))

  @catchesVentureException
  def do_sample(self, s):
    '''Sample the given expression immediately,
    without registering it as a prediction.'''
    print getValue(self._do_instruction('sample', s))

  @catchesVentureException
  def do_force(self, s):
    '''Set the given expression to the given value,
    without conditioning on it.'''
    self._do_instruction('force', s)

  @catchesVentureException
  def do_list_directives(self, _s):
    '''List active directives and their current values.'''
    for directive in self.ripl.list_directives():
      dir_id = directive['directive_id']
      dir_val = str(directive['value'])
      dir_type = directive['instruction']

      # TODO: display expressions in a sensible way

      #print "DIRECTIVE: " + str(directive)

      if dir_type == "assume":
        dir_name = directive['symbol']
        print "%d: assume %s:\t%s" % (dir_id, dir_name, dir_val)
      elif dir_type == "observe":
        dir_expr = directive['expression']
        dir_literal = dir_val
        print "%d: observe %s = \t%s" % (dir_id, dir_expr, dir_literal)
      elif dir_type == "predict":
        dir_expr = directive['expression']
        print "%d: predict %s:\t %s" % (dir_id, dir_expr, dir_val)
      else:
        assert False, "Unknown directive type found: %s" & str(directive)
  
  @catchesVentureException
  def do_clear(self, _):
    self.ripl.clear()
  
  @catchesVentureException
  def do_infer(self, s):
    '''Run inference synchronously.'''
    out = self.ripl.infer(s if s else None)
    if isinstance(out, dict):
      if len(out) > 0: print out
    else:
      print out

  @catchesVentureException
  def do_continuous_inference_status(self, s):
    '''Report status of continuous inference.'''
    print self._do_instruction('continuous_inference_status', s)

  @catchesVentureException
  def do_start_continuous_inference(self, s):
    '''Start continuous inference.'''
    self.ripl.start_continuous_inference(expToDict(parse(s)) if s else None)

  @catchesVentureException
  def do_stop_continuous_inference(self, s):
    '''Stop continuous inference.'''
    self._do_instruction('stop_continuous_inference', s)

  @catchesVentureException
  def do_get_global_logscore(self, s):
    '''Report status of continuous inference.'''
    print self._do_instruction('get_global_logscore', s)

def run_venture_console(ripl):
  RiplCmd(ripl).cmdloop()

def main():
  import venture.shortcuts as s
  ripl = s.make_puma_church_prime_ripl()
  run_venture_console(ripl)

if __name__ == '__main__': main()
