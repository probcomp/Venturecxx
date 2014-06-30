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

from cmd import Cmd
from venture.exception import VentureException

_RIPL_FUNCTIONS = [
  'get_global_logscore', 'assume','predict',
  'observe','configure','forget','report','infer',
  'clear','rollback','list_directives','get_directive',
  'force','sample','continuous_inference_status',
  'start_continuous_inference','stop_continuous_inference',
  'get_current_exception','get_state','get_logscore',
]

def make_function(ripl, instruction):
  def do_instruction(s):
    try:
      print ripl.execute_instruction('[%s %s]' % (instruction, s))
    except VentureException as e:
      print e
      if e.exception in ['parse', 'text_parse', 'invalid_argument']:
        print e.data['instruction_string']
        offset = e.data['text_index'][0]
        length = e.data['text_index'][1] - offset + 1
        underline = ''.join([' '] * offset + ['^'] * length)
        print underline
    except RuntimeError as err:
      print err
  
  return do_instruction

class RiplCmd(Cmd, object):
  def __init__(self, ripl):
    super(RiplCmd, self).__init__()
    self.ripl = ripl
    for instruction in _RIPL_FUNCTIONS:
      setattr(self, 'do_' + instruction, make_function(ripl, instruction))

if __name__ == '__main__':
  import venture.shortcuts as s
  ripl = s.make_puma_church_prime_ripl()
  RiplCmd(ripl).cmdloop()
