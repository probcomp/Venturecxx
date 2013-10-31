#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from venture.exception import VentureException
from venture.server import RiplRestServer
from venture.server import utils
from venture.shortcuts import make_venture_script_ripl, make_combined_ripl

class ServerTestCase(unittest.TestCase):

    def _request(self,endpoint,data=[]):
        r = self.client.open(path=endpoint,data=json.dumps(data),content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['content-type'], 'application/json')
        return r

    def _error_request(self,endpoint,data=[]):
        r = self.client.open(path=endpoint,data=json.dumps(data),content_type='application/json')
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.headers['content-type'], 'application/json')
        return r


class TestRestServer(ServerTestCase):

    def setUp(self):
        ripl = make_venture_script_ripl()
        args = ['assume']
        self.server = utils.RestServer(ripl,args)
        self.client = self.server.test_client()

    def test_invalid_json(self):
        r = self.client.open(path='/assume',data='moo')
        self.assertEqual(r.status_code, 500)
        self.assertEqual(json.loads(r.data)['exception'],'fatal')

    def test_valid_assume(self):
        r = self._request('/assume',['r','1'])
        self.assertEqual(json.loads(r.data), 1)

    def test_text_parse_error(self):
        r = self._error_request('/assume',['w','+++1 2'])
        self.assertEqual(json.loads(r.data)['exception'], 'text_parse')



class TestRiplRestServer(ServerTestCase):

    def setUp(self):
        ripl = make_combined_ripl()
        self.server = RiplRestServer(ripl)
        self.client = self.server.test_client()

    def test_multiple_instructions(self):
        self._request('/clear',[])
        self._request('/set_mode',['venture_script'])
        self._request('/assume',['a','1 + 2'])
        self._request('/assume',['b','1 + 2'])
        self._request('/assume',['c','a + b'])
        self._request('/set_mode',['church_prime'])
        r = self._request('/sample',['(+ c 24)'])
        self.assertEqual(json.loads(r.data), 30)


if __name__ == "__main__":
    unittest.main()