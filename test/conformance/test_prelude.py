from unittest import TestCase, SkipTest
import nose.tools as nose
from venture.test.config import get_ripl
import numpy as np
import random
import string
import operator
from numpy.testing import assert_equal

def run_containers(testfun):
  'Decorator to apply a test function to all container types.'
  @nose.make_decorator(testfun)
  def container_looper(self):
    for container in self.containers:
      testfun(self, container)
  return container_looper

class TestPrelude(TestCase):
  '''
  Provides methods for testing all routines provided by Venture "standard
  library" as given in python/lib/ripl/prelude.
  '''
  _multiprocess_can_split_ = True
  containers = ['list', 'vector', 'array']
  array_like_containers = ['array', 'vector']
  random_modes = ['numeric', 'boolean', 'mixed']
  container_length = [3,11]

  def runTest(self):
    pass

  def setUp(self):
    self.r = get_ripl()

  def reset_ripl(self):
    self.r.clear()
    self.r.load_prelude()

  def mk_random_data(self, container, mode, length = None):
    '''
    Generates random arrays / lists / vectors for use in tests.

    Parameters
    ----------
    container : str
      The type of Venture container to return. Allowed values are:
        list
        vector
        array

    mode : str
      The type of data to allow. Allowed values are:
        numeric
        boolean
        mixed (mix of numbers and quoted strings)

    length : int
      If supplied, the length of the container to return. If None, choose
      the length randomly.
    '''
    # check the arguments
    assert mode in self.random_modes
    assert container in self.containers
    # length of the container
    if length is None: length = random.choice(range(*self.container_length))
    # if it's a vector, numeric only
    if container == 'vector':
      mode = 'numeric'
    if mode == 'boolean':
      # if boolean, make a random boolean vector
      res = map(str, np.random.uniform(0,1,length) > 0.5)
    if mode == 'numeric':
      # if numeric, draw some normal random variables
      res = map(str, np.random.randn(length))
    if mode == 'mixed':
      # if mixed, draw some numbers and some strings
      res = []
      for _ in range(length):
        if np.random.uniform() > 0.5:
          res.append(str(np.random.randn()))
        else:
          nchars = random.choice(range(*self.container_length))
          thisword = ''.join(random.sample(string.letters, nchars))
          res.append('(quote {0})'.format(thisword))
    res = '({0} {1})'.format(container, ' '.join(res))
    return res

  @run_containers
  def test_is_empty(self, container):
    'Make sure that is_empty does what we expect.'
    self.reset_ripl()
    cmd_str = '(is_empty ({0}))'.format(container)
    res = self.r.sample(cmd_str)
    self.assertTrue(res)
    # create random container; make sure it's not empty
    x = self.mk_random_data(container, 'mixed')
    cmd_str = '(is_empty {0})'.format(x)
    res = self.r.sample(cmd_str)
    self.assertFalse(res)

  def test_to_list(self):
    '''
    Check that to_list converts vectors and arrays properly. The python
    representations pre and post conversion should agree, and post-conversion
    the object should satisfy "is_pair"
    '''
    for container in ['vector', 'array']:
      self.reset_ripl()
      # make the data, check it's not a list to start
      x = self.mk_random_data(container, 'mixed')
      x_python = self.array_to_list(self.r.assume('x', x), container)
      # convert, check that it does the right thing
      y_python = self.r.assume('y', ('(to_list x)'))
      self.check_type('list', 'y')
      self.assertEqual(x_python, y_python)

  def test_from_list(self):
    '''
    Check that to_array and to_vector convert lists properly.
    '''
    for container in ['vector', 'array']:
      self.reset_ripl()
      # vectors can only store numeric data
      x = self.mk_random_data('list', 'numeric')
      x_python = self.r.assume('x', x)
      # convert, check
      cmd_str = '(to_{0} x)'.format(container)
      y_python = self.array_to_list(self.r.assume('y', cmd_str), container)
      self.check_type(container, 'y')
      self.assertEqual(x_python, y_python)

  @run_containers
  def test_map(self, container):
    '''
    Test that applying "map" in Venture does the same thing as applying it
    in Python; make sure it returns data of correct type.
    '''
    # list of functions to apply (2-tuple; first is Python, second Venture)
    fncs = [(lambda x: x + 2, '(lambda (x) (+ x 2))'),
            (lambda x: x - 2, '(lambda (x) (- x 2))'),
            (lambda x: x * 3, '(lambda (x) (* x 3))'),
            (np.sin, 'sin'), (np.exp, 'exp')]
    for f_py, f_ven in fncs:
      self.reset_ripl()
      # make the assumptions
      x = self.r.assume('x', self.mk_random_data(container, 'numeric'))
      _ = self.r.assume('f', f_ven)
      # apply the mapping, make sure the results match
      mapped_py = map(f_py, x)
      mapped_ven = self.array_to_list(self.r.assume('mapped', '(map f x)'),
                                      container)
      self.assertEqual(mapped_py, mapped_ven)
      self.check_type(container, 'mapped')

  @run_containers
  def test_reduce(self, container):
    '''
    Test that applying "reduce" in Venture does same thing as in Python.
    '''
    # list of functions to apply, identity elements for the functions
    fncs = [(operator.add, '+', 0),
            (operator.mul, '*', 1)]
    for f_py, f_ven, ident in fncs:
      self.reset_ripl()
      x = self.r.assume('x', self.mk_random_data(container, 'numeric'))
      reduced_py = reduce(f_py, x, ident)
      reduced_ven = self.r.sample('(reduce {0} x {1})'.format(f_ven, ident))
      self.assertAlmostEqual(reduced_py, reduced_ven)

  @run_containers
  def test_dot(self, container):
    '''
    Test the dot product.
    '''
    self.reset_ripl()
    x = self.r.assume('x', self.mk_random_data(container, 'numeric'))
    y = self.r.assume('y', self.mk_random_data(container, 'numeric', length = len(x)))
    res_py = np.dot(x, y)
    res_ven = self.r.sample('(dot x y)')
    self.assertAlmostEqual(res_py, res_ven)

  @run_containers
  def test_math(self, container):
    '''
    Test the "sum", "product", "mean" vector aggregators.
    '''
    fncs = [(np.sum, 'sum'), (np.prod, 'prod'), (np.mean, 'mean')]
    for f_py, f_ven in fncs:
      self.reset_ripl()
      x = self.r.assume('x', self.mk_random_data(container, 'numeric'))
      res_py = f_py(x)
      res_ven = self.r.sample('({0} x)'.format(f_ven))
      self.assertAlmostEqual(res_py, res_ven)

  def test_negative(self):
    '''
    Make sure the Venture "negative" gives the negative of a number.
    '''
    self.reset_ripl()
    x = self.r.assume('x', np.random.randn())
    neg_x = self.r.sample('(negative x)')
    self.assertAlmostEqual(-1 * x, neg_x)

  def test_logit_logistic(self):
    '''
    Test that the logit and logistic functions do what they say.
    '''
    fncs = [(lambda x: 1 / (1 + np.exp(-x)), 'logistic', np.random.randn),
            (lambda x: np.log(x / (1 - x)), 'logit', np.random.uniform)]
    for f_py, f_ven, rand_fun in fncs:
      self.reset_ripl()
      x = self.r.assume('x', rand_fun())
      res_py = f_py(x)
      res_ven = self.r.sample('({0} x)'.format(f_ven))
      self.assertAlmostEqual(res_py, res_ven)

  @run_containers
  def test_scalar_mult(self, container):
    'Test that multiplying by a scalar matches Python'
    self.reset_ripl()
    x = self.r.assume('x', self.mk_random_data(container, 'numeric'))
    y = self.r.assume('y', '(uniform_continuous 0 10)')
    res_ven = self.array_to_list(self.r.assume('res', '(scalar_mult x y)'),
                                 container)
    res_py = [z * y for z in x]
    self.assertAlmostEqual(res_py, res_ven)
    self.check_type(container, 'res')

  def test_repeats(self):
    'Test that "repeat", "ones", and "zeros" work as expected'
    for fname, value in zip(['repeat', 'zeros', 'ones'],
                            [np.random.uniform(0,10), 0, 1]):
      self.reset_ripl()
      n = int(self.r.assume('n', '(uniform_discrete 1 10)'))
      _ = self.r.assume('value', value)
      x_ven = self.r.assume('x', '(repeat value n)')
      x_py = [value] * n
      self.assertAlmostEqual(x_py, x_ven)

  def test_range(self):
    'Test that range function matches python'
    self.reset_ripl()
    start = int(self.r.assume('start', '(uniform_discrete 1 10)'))
    stop = int(self.r.assume('stop', '(uniform_discrete (+ 1 start) (+ 1 10))'))
    res_py = range(start, stop)
    res_ven = self.r.assume('res', '(range start stop)')
    self.assertEqual(res_py, res_ven)

  def test_matrices(self):
    'Test that diagonal and identity matrices are as expected'
    for fname in ['eye', 'diag']:
      self.reset_ripl()
      D = self.r.assume('D', '(uniform_discrete 1 10)')
      if fname == 'diag':
        diag_entry = self.r.assume('diag_value', '(uniform_continuous 0 10)')
        res_ven = self.r.assume('res', '(diag D diag_value)')
        res_py = np.diag(np.repeat(diag_entry, D))
      else:
        diag_entry = self.r.assume('diag_value', 1)
        res_ven = self.r.assume('res', '(eye D)')
        res_py = np.eye(D)
      assert_equal(res_ven, res_py)

  def array_to_list(self, x, container):
    '''
    Vectors are returned as numpy arrays in lite backend; need to convert to
    lists to enable comparisons
    '''
    if (container == 'vector') and (self.r.backend() == 'lite'):
      return x.tolist()
    else:
      return x

  def check_type(self, in_type, varname):
    '''
    Check that the type of the output variable is what we expect
    '''
    if in_type == 'list':
      self.assertTrue(self.r.sample('(is_pair {0})'.format(varname)))
    elif in_type == 'array':
      self.assertTrue(self.r.sample('(is_array {0})'.format(varname)))
    elif in_type == 'vector':
      self.assertFalse(self.r.sample('(or (is_array {0}) (is_pair {0}))'.format(varname)))
