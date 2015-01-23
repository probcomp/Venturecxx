from nose.tools import assert_raises
from numpy.testing import assert_array_almost_equal
from os import path
import os
import pandas as pd

from venture.test.config import get_ripl
from venture.exception import VentureException

def test_timer1():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_pause)')
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_pause)')

def test_timer2():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_pause)')
  ripl.infer('(call_back timer_resume)')
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_resume)')

def test_timer3():
  ripl = get_ripl()
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_time)')

def test_timer4():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_time)')

def test_dataset_to_file():
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  infer = '''(begin
                (resample 2)
                (cycle ((mh default one 1) (peek x)) 5)
                (call_back dataset_to_file (quote test_dataset)))'''
  res = ripl.infer(infer)
  assert path.exists('test_dataset.txt')
  ds = pd.read_table('test_dataset.txt')
  assert_array_almost_equal(res.dataset(), ds, decimal = 3)
  os.remove('test_dataset.txt')
