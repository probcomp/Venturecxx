#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture import parser, ripl, sivm, server


def make_core_sivm():
    return sivm.CoreSivmCppEngine()

def make_venture_sivm():
    return sivm.VentureSivm(make_core_sivm())

def make_church_prime_ripl():
    v = make_venture_sivm()
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
    return ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})

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