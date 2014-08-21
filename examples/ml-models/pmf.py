'''
Run probabilistic matrix factorization on a toy dataset and on the MovieLens
100k dataset
'''
from os import path
import pandas as pd
from venture.unit import VentureUnit

def get_data(ntrain = None, ntest = None):
  '''
  If ntrain and ntest given, truncate the data sets to contain ntrain, ntest rows.
  '''
  data_path = path.expanduser('~/Google Drive/probcomp/pmf/ml-100k/')
  train = pd.read_table(path.join(data_path, 'ua.base'), header = 0,
                        names = ['user_id', 'item_id', 'rating', 'timestamp'])
  del train['timestamp']
  if ntrain is not None: train = train[:ntrain]
  test = pd.read_table(path.join(data_path, 'ua.test'), header = 0,
                        names = ['user_id', 'item_id', 'rating', 'timestamp'])
  del test['timestamp']
  if ntest is not None: test = test[:ntest]
  return train, test

class PMFBase(VentureUnit):
  pass

