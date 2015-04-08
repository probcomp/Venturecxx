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

# Raise Python's recursion limit, per
# http://log.brandonthomson.com/2009/07/increase-pythons-recursion-limit.html
# The reason to do this is that Venture is not tail recursive, and the
# cycle and mixture inference programs are written as recursive
# functions in Venture.
import sys
import resource
# Try to increase max stack size from 8MB to 512MB
(soft, hard) = resource.getrlimit(resource.RLIMIT_STACK)
if hard > -1:
    new_soft = max(soft, min(2**29, hard))
else:
    new_soft = max(soft, 2**29)
resource.setrlimit(resource.RLIMIT_STACK, (new_soft, hard))
# Set a large recursion depth limit
sys.setrecursionlimit(max(10**6, sys.getrecursionlimit()))

from venture import parser, ripl, sivm, server

class Backend(object):
    def trace_constructor(self): pass
    def make_engine(self, persistent_inference_trace=False):
        from venture.engine import engine
        return engine.Engine(self.name(), self.trace_constructor(), persistent_inference_trace)
    def make_core_sivm(self, persistent_inference_trace=False):
        return sivm.CoreSivm(self.make_engine(persistent_inference_trace))
    def make_venture_sivm(self, persistent_inference_trace=False):
        return sivm.VentureSivm(self.make_core_sivm(persistent_inference_trace))
    def make_church_prime_ripl(self, persistent_inference_trace=False):
        r = ripl.Ripl(self.make_venture_sivm(persistent_inference_trace),
                      {"church_prime":parser.ChurchPrimeParser.instance()})
        r.backend_name = self.name()
        return r
    def make_venture_script_ripl(self, persistent_inference_trace=False):
        r = ripl.Ripl(self.make_venture_sivm(persistent_inference_trace),
                      {"venture_script":parser.VentureScriptParser.instance()})
        r.backend_name = self.name()
        return r
    def make_combined_ripl(self, persistent_inference_trace=False):
        v = self.make_venture_sivm(persistent_inference_trace)
        parser1 = parser.ChurchPrimeParser.instance()
        parser2 = parser.VentureScriptParser.instance()
        r = ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})
        r.set_mode("church_prime")
        r.backend_name = self.name()
        return r
    def make_ripl_rest_server(self):
        return server.RiplRestServer(self.make_combined_ripl())

class Lite(Backend):
    def trace_constructor(self):
        from venture.lite import trace
        return trace.Trace
    def name(self): return "lite"

class Puma(Backend):
    def trace_constructor(self):
        from venture.puma import trace
        return trace.Trace
    def name(self): return "puma"

def backend(name = "puma"):
    if name == "lite":
        return Lite()
    if name == "puma":
        return Puma()
    raise Exception("Unknown backend %s" % name)

for (prefix, suffix) in [("make_core_", "sivm"),
                         ("make_venture_", "sivm"),
                         ("make_", "church_prime_ripl"),
                         ("make_", "venture_script_ripl"),
                         ("make_", "combined_ripl")]:
    method = prefix + suffix
    # Your complaints about metaprogramming do not fall upon deaf ears, pylint: disable=exec-used
    string2 = """
def %s():
  return backend().%s()
""" % (method, method)
    exec(string2)

    for backend_name in ["lite", "puma"]:
        function = prefix + backend_name + "_" + suffix
        string = """
def %s():
  return backend("%s").%s()
""" % (function, backend_name, method)
        exec(string)

def make_ripl_rest_server():
    r = make_combined_ripl() # Metaprogrammed.  pylint: disable=undefined-variable
    return server.RiplRestServer(r)

def make_ripl_rest_client(base_url):
    return ripl.RiplRestClient(base_url)
