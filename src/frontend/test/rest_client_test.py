#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from venture.exception import VentureException
from venture.server import RiplRestServer
from venture.shortcuts import make_venture_script_ripl, make_combined_ripl
from venture.ripl import RiplRestClient
import socket
import multiprocessing

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
        self.ripl.set_mode('venture_script')
        self.ripl.clear()
        self.ripl.assume('a','1 + 2')
        self.ripl.assume('b',' 3 + 4')
        self.ripl.set_mode('church_prime')
        self.ripl.execute_instruction('[ assume c (+ a b) ]')
        output = self.ripl.sample('c')
        self.assertEqual(output,10)


if __name__ == "__main__":
    unittest.main()