import unittest

import time
import sys
import traceback
import StringIO

from pyparsing import ParseException


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def run_test(self, code, expected_result):
        expression = self.expression
        validation_error = None
        result = None
        runtime_error = None
        parse_error = None
        try:
            result = list(expression.parseString(code, parseAll=True))
        except ParseException as e:
            parse_error = str(e)
        except Exception as e:
            re_file = StringIO.StringIO()
            traceback.print_exception(*sys.exc_info(), file=re_file)
            runtime_error = re_file.getvalue().replace('\n','\n'+' '*18)
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
