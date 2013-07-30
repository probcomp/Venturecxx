#!/usr/bin/env python
# -*- coding: utf-8 -*-

import new
from flask import Flask, request
import requests
import json

from venture.exception import VentureException

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


class RestServer(Flask):
    def __init__(self, obj, args):
        super(RestServer,self).__init__(str(obj.__class__))
        for name in args:
            def mk_closure(name):
                obj_function = getattr(obj,name)
                def f():
                    try:
                        args = self._get_json()
                        ret_value = obj_function(*args)
                        return self._json_response(ret_value,200)
                    except VentureException as e:
                        return self._json_response(e.to_json_object(),500)
                    except Exception as e:
                        ve = VentureException('fatal',str(e))
                        return self._json_response(ve.to_json_object(),500)
                return f
            f = mk_closure(name)
            f.methods = ['GET','POST']
            self.add_url_rule('/'+name,name,f)

    def _get_json(self):
        # cannot pass it as json for some reason,
        # so need to force it here.
        print ("data: " + request.data)
        print ("json: " + str(request.json))
        #return request.get_json(force=True)
        
        j = json.loads(request.data)
        import pdb; pdb.set_trace()
        return j

    def _json_response(self, j, status):
        s = json.dumps(j)
        h = {'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*'}
        return s,status,h
