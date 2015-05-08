import scipy
import numpy as np
import pandas as pd
from os.path import join, exists
import os
from shutil import rmtree
from matplotlib import pyplot as plt

from venture.lite.discrete import DiscretePSP
from venture.lite import value as v
from venture.lite.builtin import typed_nr
import venture.ripl.utils as u

def __venture_start__(ripl):
  ripl.bind_callback('print_this', print_this)

def print_this(_, ds):
  ds = u.strip_types(ds)[0].asPandas()
  counts = ds.n_balls.value_counts()
  max = counts.index.max()
  print counts[range(0, int(max + 1))].fillna(0)
  
  
