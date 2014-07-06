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

from venture import parser, ripl, sivm, server

class Backend(object):
    def make_core_sivm(self): pass
    def make_venture_sivm(self):
        return sivm.VentureSivm(self.make_core_sivm())
    def make_church_prime_ripl(self):
        r = ripl.Ripl(self.make_venture_sivm(), {"church_prime":parser.ChurchPrimeParser.instance()})
        r.backend_name = self.name()
        return r
    def make_venture_script_ripl(self):
        r = ripl.Ripl(self.make_venture_sivm(), {"venture_script":parser.VentureScriptParser.instance()})
        r.backend_name = self.name()
        return r
    def make_combined_ripl(self):
        v = self.make_venture_sivm()
        parser1 = parser.ChurchPrimeParser.instance()
        parser2 = parser.VentureScriptParser.instance()
        r = ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})
        r.set_mode("church_prime")
        r.backend_name = self.name()
        return r
    def make_ripl_rest_server(self):
        return server.RiplRestServer(self.make_combined_ripl())

class CXX(Backend):
    def make_core_sivm(self):
        from venture.cxx import engine
        return sivm.CoreSivm(engine.Engine())
    def name(self): return "cxx"

class Lite(Backend):
    def make_core_sivm(self):
        from venture.lite import engine
        return sivm.CoreSivm(engine.Engine())
    def name(self): return "lite"

class Puma(Backend):
    def make_core_sivm(self):
        from venture.puma import engine
        return sivm.CoreSivm(engine.Engine())
    def name(self): return "puma"

def backend(name = "puma"):
    if name == "lite":
        return Lite()
    if name == "cxx":
        return CXX()
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

    for backend_name in ["lite", "puma", "cxx"]:
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

# value shortcuts

def val(t,v):
    return {"type":t,"value":v}

def symbol(s):
    return val("symbol", s)

def number(v):
    return val("number",v)

def boolean(v):
    return val("boolean",v)

def real(v):
    return val("real",v)

def count(v):
    return val("count",v)

def probability(v):
    return val("probability",v)

def atom(v):
    return val("atom",v)

def smoothed_count(v):
    return val("smoothed_count",v)

def simplex_point(v):
    return val("simplex_point",v)
