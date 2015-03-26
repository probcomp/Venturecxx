from nose.tools import eq_
from re import search

from venture.test.config import get_ripl, broken_in, capture_output

def extract_integer(captured):
  'Extract the Venture integer from a captured print'
  res = search('VentureInteger\((.*)\)', captured) #pylint: disable=W1401
  return int(res.group(1))

@broken_in("puma", "TODO: implement in-model debug print in puma")
def test_print1():
  'Make sure that print prints the correct values by intercepting output'
  ripl = get_ripl()
  x = ripl.assume('x', '(uniform_discrete 1 10)')
  y = ripl.assume('y', '(uniform_discrete 1 10)')
  program = ('[SAMPLE (+ (print x (quote x)) (print y (quote y)))]')
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_x, captured_y = map(extract_integer, captured.splitlines())
  eq_(x, captured_x)
  eq_(y, captured_y)
  eq_(res_value, captured_x + captured_y)

@broken_in("puma", "TODO: implement in-model debug print in puma")
def test_print2():
  'Another test for consistency by intercepting output'
  ripl = get_ripl()
  program = '''[SAMPLE (+ (print (uniform_discrete 1 10) (quote x))
                          (print (uniform_discrete 1 10) (quote y)))]'''
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_values = map(extract_integer, captured.splitlines())
  eq_(res_value, sum(captured_values))
