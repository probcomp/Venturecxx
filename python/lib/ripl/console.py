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

import sys
from venture.exception import VentureException

def run_venture_console(ripl):
  while True:
    sys.stdout.write('>>> ')
    current_line = sys.stdin.readline()
    if not current_line:
      print ''
      print "End of input reached."
      print "Moriturus te saluto."
      break
    
    current_line = current_line.strip()
    if current_line == "":
      continue
    
    try:
      print ripl.execute_instruction('[%s]' % current_line)
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

if __name__ == '__main__':
  import venture.shortcuts as s
  ripl = s.make_puma_church_prime_ripl()
  run_venture_console(ripl)
