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
import unittest

import sys
import traceback
import StringIO

from pyparsing import ParseException, ParseResults

from venture.exception import VentureException

def _unpack(l):
    if isinstance(l['value'], (list, tuple, ParseResults)):
        return [_unpack(x) for x in l['value']]
    return l['value']

class ParserTestCase(unittest.TestCase):
    def _run_test(self, code, expected_result, expression, legacy):
        validation_error = None
        result = None
        runtime_error = None
        parse_error = None
        try:
            result = list(expression.parseString(code, parseAll=True))
        except (ParseException, VentureException) as e:
            parse_error = str(e)
        except Exception as e:
            re_file = StringIO.StringIO()
            traceback.print_exception(*sys.exc_info(), file=re_file)
            runtime_error = re_file.getvalue().replace('\n','\n'+' '*18)
        if legacy==True and result!=None:
            result = [_unpack(x) for x in result]
        match = result == expected_result
        message = ['']
        message.append( "code:            " + code.replace('\n','\n'+' '*18))
        message.append( "got:             " + str(result))
        message.append( "expected:        " + str(expected_result))
        if validation_error:
            message.append( "validation error:" + str(validation_error))
        if runtime_error:
            message.append( "runtime error:   " + str(runtime_error))
        if parse_error:
            message.append( "parse error:     " + str(parse_error))
        message.append( "match:           " + str(match))
        message.append( '' )
        if not match or validation_error or runtime_error:
            self.fail('\n'.join(message))
        return match

    def run_test(self, code, expected_result):
        self._run_test(code, expected_result, self.expression, legacy=False)
    run_test.__test__ = False

    def run_legacy_test(self, code, expected_result, name):
        e = getattr(self.p, name)
        self._run_test(code, expected_result, e, legacy=True)
    run_legacy_test.__test__ = False
