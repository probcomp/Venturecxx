from unittest import TestCase
from venture.shortcuts import (make_lite_church_prime_ripl, 
                               make_puma_church_prime_ripl)


class TestPrelude(TestCase):
  '''
  Provides methods for testing all routines provided by Venture "standard 
  library" as given in python/lib/ripl/prelude. This is a base class for two
  subclasses TestPreludePuma and TestPreludeLite; these provide different
  setUp methods to test the two backends respectively.
  ''' 
  _multiprocess_can_split_ = True

class TestPreludePuma(TestPrelude):
  def setUp(self):
    self.v = make_church_prime_ripl()

class TestPreludeLite(TestPrelude):
  def setUp(self):
    self.v = make_lite_church_prime_ripl()
