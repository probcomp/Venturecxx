# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
import socket
import multiprocessing
from nose import SkipTest
from nose.plugins.attrib import attr

from venture.server import RiplRestServer
from venture.shortcuts import make_combined_ripl
from venture.ripl import RiplRestClient

# from stackoverflow
# prone to race conditions, but its good enough for now
def get_open_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

class ClientTestCase(unittest.TestCase):
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
class TestRiplRestClient(ClientTestCase):
    def setUp(self):
        self.local_ripl = make_combined_ripl()
        self.server = RiplRestServer(self.local_ripl)
        port = get_open_port()
        def run_server():
            self.server.run(host='localhost',port=port)
        self.server_thread = multiprocessing.Process(target=run_server)
        self.server_thread.start()
        self.ripl = RiplRestClient('http://localhost:'+str(port))

    def tearDown(self):
        self.server_thread.terminate()
        self.server_thread.join()

    def test_multiple_instructions(self):
        raise SkipTest("Fails sporadically:  Issue: https://app.asana.com/0/9277419963067/10034153747714")
        self.ripl.set_mode('venture_script')
        self.ripl.clear()
        self.ripl.assume('a','1 + 2')
        self.ripl.assume('b',' 3 + 4')
        self.ripl.set_mode('church_prime')
        self.ripl.execute_instruction('[ assume c (+ a b) ]')
        output = self.ripl.predict('c')
        self.assertEqual(output,10)
