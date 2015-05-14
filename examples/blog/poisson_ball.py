import pandas as pd
import numpy as np
from json import load
from scipy import stats

import venture.ripl.utils as u

def __venture_start__(ripl):
  ripl.bind_callback('data_dump', data_dump)

def unwrap(x):
  return u.strip_types(x)[0]

def data_dump(_, ds, file_name):
  ds = unwrap(ds).asPandas()
  file_name = unwrap(file_name)
  ds.to_csv(file_name + '.csv',
            index = False)
