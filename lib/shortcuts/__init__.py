#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture import parser, ripl, vim, server


def make_core_vim():
    return vim.CoreVimCppEngine()

def make_venture_vim():
    return vim.VentureVim(make_core_vim())

def make_venture_lisp_ripl():
    v = make_venture_vim()
    parser1 = parser.VentureLispParser()
    return ripl.Ripl(v,{"venture_lisp":parser1})

def make_venture_script_ripl():
    v = make_venture_vim()
    parser1 = parser.VentureScriptParser()
    return ripl.Ripl(v,{"venture_script":parser1})

def make_combined_ripl():
    v = make_venture_vim()
    parser1 = parser.VentureLispParser()
    parser2 = parser.VentureScriptParser()
    return ripl.Ripl(v,{"venture_lisp":parser1, "venture_script":parser2})


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
