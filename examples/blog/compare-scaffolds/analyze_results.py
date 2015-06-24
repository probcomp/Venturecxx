import os
import pandas as pd
import seaborn as sns
from string import lower
from matplotlib import pyplot as plt

def collect_results():
  results_path = 'results'
  files = [results_path + '/' + x for x in os.listdir(results_path)]
  results = pd.concat(map(collect_result_file, files)).reset_index(drop = True)
  column_order = ['set_model', 'thunks', 'predict', 'client',
                  'size', 'index', 'brush_nodes']
  results = results[column_order]
  results.to_csv(results_path + '/' + 'result_summary.csv',
                 index = False)
  
def collect_result_file(fname):
  # Data munging. This isn't pretty but I've gotta get this done kinda fast right now
  indices = []
  brush_nodes = []
  with open(fname) as f:
    set_model = f.readline().strip()
    thunks = eval(f.readline().strip().replace('Using thunks: ', ''))
    predict = eval(f.readline().strip().replace('Predicting tokens: ', ''))
    client= eval(f.readline().strip().replace('Adding client code: ', ''))
    size = float(f.readline().strip().replace('Size: ', ''))
    line = f.readline()
    while line:
      if 'Index' in line:
        indices.append(float(line.strip().replace('Index:', '')))
      elif 'brush nodes' in line:
        brush_nodes.append(int(line.strip().replace('# brush nodes: ', '')))
      line = f.readline()
    return pd.DataFrame(dict(set_model = set_model,
                             thunks = thunks,
                             predict = predict,
                             client = client,
                             size = size,
                             index = indices,
                             brush_nodes = brush_nodes))

def plot_brush_sizes():
  ds = pd.read_csv('results/result_summary.csv')
  for names, df in ds.groupby(['set_model', 'thunks', 'predict', 'client']):
    plot_brush(names, df)

def plot_brush(names, df):
  fig, ax = plt.subplots(1)
  df.groupby('size').plot(x = 'index', y = 'brush_nodes',
                          legend = False, ax = ax)
  ax.legend(sorted(df['size'].unique()), title = 'Set size')
  ax.set_xlabel('Index of set selector')
  ax.set_ylabel('Brush size')
  title = '{0}. Thunks: {1}. Predict: {2}.'
  title = title.format(*names[:-1])
  ax.set_title(title)
  fname ='{0}-thunks-{1}-predict-{2}.png'.format(*[lower(str(x)) for x in names[:-1]])
  fig.savefig('results/' + fname)
  
if __name__ == '__main__':
  collect_results()
  plot_brush_sizes()
