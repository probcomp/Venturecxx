from unittest import TestCase
from venture.shortcuts import (make_lite_church_prime_ripl, 
                               make_puma_church_prime_ripl)
import numpy as np
import random
import string

def run_containers(testfun):
  'Decorator to apply a test function to all container types.'
  def container_looper(self):
    for container in self.containers: 
      testfun(self, container)
  return container_looper

class PreludeTestBase(TestCase):
  '''
  Provides methods for testing all routines provided by Venture "standard 
  library" as given in python/lib/ripl/prelude. This class itself is never
  used to run tests; it is a base class for two subclasses TestPreludePuma 
  and TestPreludeLite; these provide different setUp methods to test the two 
  backends respectively.
  ''' 
  _multiprocess_can_split_ = True
  containers = ['list', 'vector', 'array']
  array_like_containers = ['array', 'vector']
  random_modes = ['numeric', 'boolean', 'mixed']
  container_length = [3,11]

  def runTest(self):
    pass

  def reset_ripl(self):
    self.v.clear()
    self.v.load_prelude()

  def mk_random_data(self, container, mode):
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
    '''
    # check the arguments
    errstr = 'mode must be one of PreludeTestBase.random_modes.'
    assert mode in self.random_modes, errstr
    errstr = 'container must be one of PreludeTestBase.containers.'
    assert container in self.containers, errstr
    # length of the container
    l = random.choice(range(*self.container_length))
    if mode == 'boolean':
      # if boolean, make a random boolean vector
      res = map(str, np.random.uniform(0,1,l) > 0.5)
    if mode == 'numeric':
      # if numeric, draw some normal random variables
      res = map(str, np.random.randn(l))
    if mode == 'mixed':
      # if mixed, draw some numbers and some strings
      res = []
      for _ in range(l):
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
    res = self.v.sample(cmd_str)
    msg = 'Calling is_empty on empty {0} does not return True.'
    self.assertTrue(res, msg = msg.format(container))
    # create random container; make sure it's not empty
    x = self.mk_random_data(container, 'mixed')
    cmd_str = '(is_empty {0})'.format(x)
    res = self.v.sample(cmd_str)
    msg = 'Calling is_empty on non-empty {0} does not return False.'
    self.assertFalse(res, msg = msg.format(container))

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
      x_python = self.v.assume('x', x)
      errstr = ('Input should have been {0} but passed is_pair.'.
                format(container))
      self.assertFalse(self.v.sample('(is_pair x)'), errstr)
      # convert, check that it does the right thing
      y_python = self.v.assume('y', ('(to_list x)'))
      errstr = 'Output should be list, but failed is_pair'
      self.assertTrue(self.v.sample('(is_pair y)'), errstr)
      errstr = 'Input and output should look identical in Python.'
      self.assertEqual(x_python, y_python)

  def test_from_list(self):
    '''
    Check that to_array and to_vector convert lists properly. Small hitch:
    vectors satisfy is_array in lite backend but not in Puma.
    '''
    for container in ['vector', 'array']:
      self.reset_ripl()
      # make the data, check it's not an array to start
      x_python = self.v.assume('x', x)
      x = self.mk_random_data('list', 'mixed')
      errstr = 'Input should have been list, but passed is_vector.'
      self.assertFalse(self.v.sample('(is_array x)'), errstr)
      # convert, check
      cmd_str = '(to_{0} x)'.format(container)
      y_python = self.v.assume('y', cmd_str)

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
      x = self.v.assume('x', self.mk_random_data(container, 'numeric'))
      _ = self.v.assume('f', f_ven)
      # apply the mapping, make sure the results match
      mapped_py = map(f_py, x)
      mapped_ven = self.v.assume('mapped', '(map f x)')
      errstr = ('Results for Python and Venture mappings of function "{0}" differ.'.
                format(f_ven))
      self.assertEqual(mapped_py, mapped_ven, msg = errstr)

  def test_reduce(self, container):
    '''
    Test that applying "reduce" in Venture does same thing as in Python.
    '''
    pass


  def check_type(self, in_type, varname):
    '''
    Check that the type of the output variable is what we expect
    '''
    pass



class TestPreludePuma(PreludeTestBase):
  '''
  Adds a setUp method do start up the lite ripl.
  '''
  def setUp(self):
    self.v = make_puma_church_prime_ripl()

class TestPreludeLite(PreludeTestBase):
  '''
  Adds a setUp method to start the puma ripl.
  '''
  def setUp(self):
    self.v = make_lite_church_prime_ripl()

if __name__ == '__main__':
  # self = TestPreludePuma()
  self = TestPreludeLite()
  self.setUp()
  # self.test_is_empty()

