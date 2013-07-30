#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.shortcuts import *

server = make_ripl_rest_server()
server.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)
