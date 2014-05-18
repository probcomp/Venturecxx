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
        return ripl.Ripl(self.make_venture_sivm(), {"church_prime":parser.ChurchPrimeParser.instance()})
    def make_venture_script_ripl(self):
        return ripl.Ripl(self.make_venture_sivm(), {"venture_script":parser.VentureScriptParser.instance()})
    def make_combined_ripl(self):
        v = self.make_venture_sivm()
        parser1 = parser.ChurchPrimeParser.instance()
        parser2 = parser.VentureScriptParser.instance()
        r = ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})
        r.set_mode("church_prime")
        return r
    def make_ripl_rest_server(self):
        return server.RiplRestServer(self.make_combined_ripl())

class CXX(Backend):
    def make_core_sivm(self):
        from venture.cxx import engine
        return sivm.CoreSivm(engine.Engine())

class Lite(Backend):
    def make_core_sivm(self):
        from venture.lite import engine
        return sivm.CoreSivm(engine.Engine())

class Puma(Backend):
    def make_core_sivm(self):
        from venture.puma import engine
        return sivm.CoreSivm(engine.Engine())

def backend(name = "puma"):
    if name == "lite":
        return Lite()
    if name == "cxx":
        return CXX()
    if name == "puma":
        return Puma()
    raise Exception("Unknown backend %s" % name)

def make_core_cxx_sivm():
    from venture.cxx import engine
    return sivm.CoreSivm(engine.Engine())

def make_core_lite_sivm():
    from venture.lite import engine
    return sivm.CoreSivm(engine.Engine())

def make_core_puma_sivm():
    from venture.puma import engine
    return sivm.CoreSivm(engine.Engine())

make_core_sivm = make_core_puma_sivm

def make_venture_cxx_sivm():
    return sivm.VentureSivm(make_core_cxx_sivm())

def make_venture_lite_sivm():
    return sivm.VentureSivm(make_core_lite_sivm())

def make_venture_puma_sivm():
    return sivm.VentureSivm(make_core_puma_sivm())

def make_venture_sivm():
    return sivm.VentureSivm(make_core_sivm())

def make_church_prime_ripl():
    v = make_venture_sivm()
    parser1 = parser.ChurchPrimeParser.instance()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_cxx_church_prime_ripl():
    v = make_venture_cxx_sivm()
    parser1 = parser.ChurchPrimeParser.instance()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_lite_church_prime_ripl():
    v = make_venture_lite_sivm()
    parser1 = parser.ChurchPrimeParser.instance()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_puma_church_prime_ripl():
    v = make_venture_puma_sivm()
    parser1 = parser.ChurchPrimeParser.instance()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_venture_script_ripl():
    v = make_venture_sivm()
    parser1 = parser.VentureScriptParser.instance()
    return ripl.Ripl(v,{"venture_script":parser1})

def make_combined_ripl():
    v = make_venture_sivm()
    parser1 = parser.ChurchPrimeParser.instance()
    parser2 = parser.VentureScriptParser.instance()
    r = ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})
    r.set_mode("church_prime")
    return r

def make_ripl_rest_server():
    r = make_combined_ripl()
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
