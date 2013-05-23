#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request
import inspect
import json

from venture.exception import VentureException

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
        if request.headers['content-type'] == 'application/json':
            return request.json
        else:
            raise RuntimeError("Invalid JSON request. Content type should be application/json.")

    def _json_response(self, j, status):
        s = json.dumps(j)
        h = {'Content-Type':'application/json'}
        return s,status,h
