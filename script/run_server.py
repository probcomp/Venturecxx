#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from venture.shortcuts import *

port = 8082
if len(sys.argv) > 1:
    port = int(sys.argv[1])

server = make_ripl_rest_server()
server.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
