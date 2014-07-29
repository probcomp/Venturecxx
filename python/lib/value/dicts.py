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
# -*- coding: utf-8 -*-

# Abstraction barrier for the Python dict representation of Venture values.


def val(t,v):
    return {"type":t,"value":v}

def number(v):
    return val("number",v)

def real(v):
    return val("real",v)

def integer(v):
    return val("integer",v)

def probability(v):
    return val("probability",v)

def atom(v):
    return val("atom",v)

def boolean(v):
    return val("boolean",v)

def symbol(s):
    return val("symbol",s)

def blob(v):
    return val("blob",v)

def list(vs):
    return val("list", vs)

def improper_list(vs, tail):
    return val("improper_list", (vs, tail))

def array(vs):
    return val("array", vs)

def array_unboxed(vs, subtype):
    ret = val("array_unboxed", vs)
    ret["subtype"] = subtype
    return ret

def vector(vs):
    return val("vector", vs)

def simplex(vs):
    return val("simplex", vs)

def matrix(vs):
    import numpy as np
    return val("matrix", np.asarray(vs))

def symmetric_matrix(vs):
    import numpy as np
    return val("symmetric_matrix", np.asarray(vs))

def quote(v):
    return [symbol("quote"), v]

