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
from venture.ripl.utils import run_venture_console

def make_core_sivm():
    return sivm.CoreSivmCxx()

def make_core_lite_sivm():
    return sivm.CoreSivmLite()

def make_core_jventure_sivm():
    return sivm.CoreSivmJVenture()

def make_venture_sivm():
    return sivm.VentureSivm(make_core_sivm())

def make_venture_lite_sivm():
    return sivm.VentureSivm(make_core_lite_sivm())

def make_venture_jventure_sivm():
    return sivm.VentureSivm(make_core_jventure_sivm())

def make_church_prime_ripl():
    v = make_venture_sivm()
    parser1 = parser.ChurchPrimeParser()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_lite_church_prime_ripl():
    v = make_venture_lite_sivm()
    parser1 = parser.ChurchPrimeParser()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_jventure_church_prime_ripl():
    v = make_venture_jventure_sivm()
    parser1 = parser.ChurchPrimeParser()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_venture_script_ripl():
    v = make_venture_sivm()
    parser1 = parser.VentureScriptParser()
    return ripl.Ripl(v,{"venture_script":parser1})

def make_combined_ripl():
    v = make_venture_sivm()
    parser1 = parser.ChurchPrimeParser()
    parser2 = parser.VentureScriptParser()
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
