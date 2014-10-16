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

import new
from flask import Flask, request
import requests
import json

from venture.exception import VentureException
from crossdomain import crossdomain

class RestClient(object):
    def __init__(self, base_url, function_list):
        self.base_url = base_url.rstrip('/') + '/'
        for name in function_list:
            def mkfunction(name):
                def f(self,*args):
                    try:
                        data = json.dumps(args)
                        headers = {'content-type':'application/json'}
                        r = requests.post(self.base_url + name, data=data, headers=headers)
                        if r.status_code == 200:
                            return r.json()
                        else:
                            raise VentureException.from_json_object(r.json())
                    except Exception as e:
                        raise VentureException('fatal',str(e))
                return f
            unbound_function = mkfunction(name)
            bound_function = new.instancemethod(unbound_function,self,self.__class__)
            setattr(self,name,bound_function)

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy
        if isinstance(obj, numpy.ndarray) and obj.ndim == 1:
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class RestServer(Flask):
    def __init__(self, obj, args):
        super(RestServer,self).__init__(str(obj.__class__))
        for name in args:
            def mk_closure(name):
                obj_function = getattr(obj,name)
                @crossdomain(origin='*', headers=['Content-Type'])
                def f():
                    try:
                        args = self._get_json()
                        ret_value = obj_function(*args)
                        return self._json_response(ret_value,200)
                    except VentureException as e:
                        print e
                        return self._json_response(e.to_json_object(),500)
                    except Exception as e:
                        ve = VentureException('fatal',str(e))
                        print ve
                        return self._json_response(ve.to_json_object(),500)
                return f
            f = mk_closure(name)
            f.methods = ['GET','POST']
            self.add_url_rule('/'+name,name,f)

    def _get_json(self):
        return request.get_json()

    def _json_response(self, j, status):
        s = json.dumps(j, cls=NumpyAwareJSONEncoder)
        h = {'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*'}
        return s,status,h
