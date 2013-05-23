#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.server.rest_server import RestServer
from venture.ripl.utils import _RIPL_FUNCTIONS


class RiplRestServer(RestServer):
    def __init__(self,ripl):
        super(RiplRestServer,self).__init__(ripl,_RIPL_FUNCTIONS)
