# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-


from venture.server.utils import RestClient
from venture.ripl.utils import _RIPL_FUNCTIONS

class RiplRestClient(RestClient):
    def __init__(self, base_url):
        super(RiplRestClient, self).__init__(base_url, _RIPL_FUNCTIONS)

    # TODO: Somehow share this with ripl.py
    def print_directives(self, *args):
        for directive in self.list_directives(*args):
            dir_id = int(directive['directive_id'])
            dir_val = str(directive['value'])
            dir_type = directive['instruction']
            dir_text = self._get_raw_text(dir_id)
            
            if dir_type == "assume":
                print "%d: %s:\t%s" % (dir_id, dir_text, dir_val)
            elif dir_type == "observe":
                print "%d: %s" % (dir_id, dir_text)
            elif dir_type == "predict":
                print "%d: %s:\t %s" % (dir_id, dir_text, dir_val)
            else:
                assert False, "Unknown directive type found: %s" % str(directive)

