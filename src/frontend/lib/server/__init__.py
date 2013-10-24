#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.server import utils
from venture.ripl.utils import _RIPL_FUNCTIONS


class RiplRestServer(utils.RestServer):
    def __init__(self,ripl):
        super(RiplRestServer,self).__init__(ripl,_RIPL_FUNCTIONS)