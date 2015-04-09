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

import os.path
from venture.test.config import get_ripl

plugin_name = os.path.dirname(os.path.abspath(__file__)) + "/plugin.py"

def testPluginsLoad():
  r = get_ripl()
  r.load_plugin(plugin_name)
  r.infer("(call_back foo)")

def testPluginsLoad2():
  r = get_ripl()
  r.infer("(load_plugin (quote symbol<\"" + plugin_name + "\">))")
  r.infer("(call_back foo)")

def testPluginsLoad3():
  r = get_ripl()
  r.infer("""(do
  (seven <- (load_plugin (quote symbol<"%s">)))
  (assert (eq 7 seven)))""" % (plugin_name,))
