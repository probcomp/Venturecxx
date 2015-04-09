#! /usr/bin/env python

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

'Fill out patterns template to create patterns for YAML-tmLanguage file'

from string import Template
import re
from sys import argv

from venture.lite.builtin import builtInSPsList
from venture.lite.inference_sps import inferenceSPsList
import venture.sivm.macro # To register the macros
from venture.sivm.macro_system import macros

def main(arg):
  if arg == 'syntax':
    get_syntax()
  elif arg == 'indent':
    get_indent()

def get_syntax():
  with open('tmLanguage-template') as f:
    template = Template(f.read())
  subs = dict(model_sps = model_sps(),
              inference_sps = inference_sps(),
              model_macros = model_macros(),
              inference_macros = inference_macros())
  subs.update(parse_grammar())
  subs_pretty = dict([(k, prettify(v)) for k, v in subs.iteritems()])
  spec = template.substitute(**subs_pretty)
  print spec

def get_indent():
  print '"(' + prettify(sorted(set(model_macros() + inference_macros()))) + ')$"'

def model_sps():
  return [x[0] for x in builtInSPsList]

def inference_sps():
  return [x[0] for x in inferenceSPsList]

def model_macros():
  names = []
  for macro in macros:
    if macro.desc is not None:
      desc = macro.desc
      pattern = re.compile('\([^ ]+')
      match = pattern.search(desc)
      names.append(match.group(0)[1:])
  return names

def inference_macros():
  # TODO The inference macros are now expanded by the sivm too, and
  # distinguished by a flag.
  return []

def prettify(xs):
  return '|'.join(sorted(xs))

def parse_grammar():
  with open('../../python/lib/parser/church_prime/grammar.y') as f:
    grammar = f.readlines()
  return dict(directives = search_for(grammar, 'directive'),
              commands = search_for(grammar, 'command'),
              literals = search_for(grammar, 'literal'))

def search_for(grammar, matchstr):
  pattern = re.compile('^{0}\([^)]+\)'.format(matchstr))
  res = []
  for line in grammar:
    match = pattern.search(line)
    if match:
      res.append(match.group(0).split('(')[1][:-1])
  return res

if __name__ == '__main__':
  arg = argv[1]
  main(arg)
