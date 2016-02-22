# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import unittest
import json
from nose.plugins.attrib import attr

from venture.server import RiplRestServer
from venture.server import utils
from venture.shortcuts import Lite

class ServerTestCase(unittest.TestCase):

    def _request(self,endpoint,data=None):
        if data is None: data = []
        r = self.client.open(path=endpoint,data=json.dumps(data),content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['content-type'], 'application/json')
        return r

    def _error_request(self,endpoint,data=None):
        if data is None: data = []
        r = self.client.open(path=endpoint,data=json.dumps(data),content_type='application/json')
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.headers['content-type'], 'application/json')
        return r


# TODO Not really backend independent, but doesn't test the backend much.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestRestServer(ServerTestCase):

    def setUp(self):
        ripl = Lite().make_venture_script_ripl()
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



# TODO Not really backend independent, but doesn't test the backend much.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestRiplRestServer(ServerTestCase):

    def setUp(self):
        ripl = Lite().make_combined_ripl()
        self.server = RiplRestServer(ripl)
        self.client = self.server.test_client()

    def test_multiple_instructions(self):
        self._request('/clear',[])
        self._request('/set_mode',['venture_script'])
        self._request('/assume',['a','1 + 2'])
        self._request('/assume',['b','1 + 2'])
        self._request('/assume',['c','a + b'])
        self._request('/set_mode',['church_prime'])
        r = self._request('/predict',['(+ c 24)'])
        self.assertEqual(json.loads(r.data), 30)


