from StringIO import StringIO
from nose.tools import eq_
import sys
from re import search

from venture.test.config import get_ripl, broken_in

def capture_output(ripl, program):
  'Capture stdout; return the string headed for stdout and the result of the computation'
  old_stdout = sys.stdout
  captured = StringIO()
  sys.stdout = captured
  res = ripl.execute_program(program)
  sys.stdout = old_stdout
  return res, captured.getvalue()

def extract_integer(captured):
  'Extract the Venture integer from a captured printf'
  res = search('VentureInteger\((.*)\)', captured) #pylint: disable=W1401
  return int(res.group(1))

@broken_in("puma", "TODO: implement in PUMA")
def test_printf1():
  'Make sure that printf prints the correct values by intercepting output'
  ripl = get_ripl()
  x = ripl.assume('x', '(uniform_discrete 1 10)')
  y = ripl.assume('y', '(uniform_discrete 1 10)')
  program = ('[SAMPLE (+ (printf x (quote x)) (printf y (quote y)))]')
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_x, captured_y = map(extract_integer, captured.splitlines())
  eq_(x, captured_x)
  eq_(y, captured_y)
  eq_(res_value, captured_x + captured_y)

@broken_in("puma", "TODO: implement in PUMA")
def test_printf2():
  'Another test for consistency by intercepting output'
  ripl = get_ripl()
  program = '''[SAMPLE (+ (printf (uniform_discrete 1 10) (quote x))
                          (printf (uniform_discrete 1 10) (quote y)))]'''
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_values = map(extract_integer, captured.splitlines())
  eq_(res_value, sum(captured_values))
