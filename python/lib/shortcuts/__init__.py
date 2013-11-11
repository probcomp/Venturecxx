#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture import parser, ripl, sivm, server

default_backend = "cxx"

def make_core_sivm(backend = default_backend):
    if backend == "cppengine":
        return sivm.CoreSivmCppEngine()
    elif backend == "cxx":
        return sivm.CoreSivmCxx()
    else:
        raise Exception("Undefined backend.")

def make_venture_sivm(backend = default_backend):
    return sivm.VentureSivm(make_core_sivm(backend))

def make_church_prime_ripl(backend = default_backend):
    v = make_venture_sivm(backend)
    parser1 = parser.ChurchPrimeParser()
    return ripl.Ripl(v,{"church_prime":parser1})

def make_venture_script_ripl(backend = default_backend):
    v = make_venture_sivm(backend)
    parser1 = parser.VentureScriptParser()
    return ripl.Ripl(v,{"venture_script":parser1})

def make_combined_ripl(backend = default_backend):
    v = make_venture_sivm(backend)
    parser1 = parser.ChurchPrimeParser()
    parser2 = parser.VentureScriptParser()
    r = ripl.Ripl(v,{"church_prime":parser1, "venture_script":parser2})
    r.set_mode("church_prime")
    return r

def make_ripl_rest_server(backend = default_backend):
    r = make_combined_ripl(backend)
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
