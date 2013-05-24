#!/usr/bin/env python
# -*- coding: utf-8 -*-


from venture.server.utils import RestClient
from venture.ripl.utils import _RIPL_FUNCTIONS

class RiplRestClient(RestClient):
    def __init__(self, base_url):
        super(RiplRestClient, self).__init__(base_url, _RIPL_FUNCTIONS)