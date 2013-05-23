#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import new
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
