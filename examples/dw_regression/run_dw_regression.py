'''
Actually run the code in dw_regression and make outputs. Disclaimer: had to
write this to get some stuff done quickly, so this code is a hot mess. Will
refactor if turns out to be useful for more stuff.
'''

import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from dw_regression import LinearRegression, LogisticRegression
import warnings
import cPickle as pkl
from os import path
import os

def test_asymptotics(outdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/asymptotics'):
  '''
  check that things scale linearly
  '''
  warnings.filterwarnings('ignore', category = DeprecationWarning)
  infers = ['(meanfield default one 10 5)',
            '(mh default one 1)']
  dims = np.hstack([np.array([1]), np.r_[10:110:10]])
  # for model in LinearRegression, LogisticRegression:
  for model in [LogisticRegression]:
    print model.__name__
    lr = model(backend = 'lite', no_ripls = 1,
               local_mode = True)
    res = {}
    for infer in infers:
      print infer
      infer_name = infer.split(' ')[0][1:]
      res[infer_name] = pd.Series(index = dims)
      for dim in dims: 
        print dim
        lr.build_model(dim, False)
        lr.simulate_data(10,10)
        lr.evaluate_inference(2, infer)
        res[infer_name][dim] = lr.inference_results['sweep time (s)'].mean()
    res = pd.DataFrame(res)
    res.index.name = 'p'
    res.to_csv(path.join(outdir, model.__name__.lower() + '.txt'),
               sep = '\t')

def plot_asymptotics(wkdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/asymptotics/'):
  '''
  plot the results
  '''
  linreg = pd.read_table(path.join(wkdir, 'linearregression.txt'),
                         index_col = 'p')
  logreg = pd.read_table(path.join(wkdir, 'logisticregression.txt'),
                         index_col = 'p')
  mh = pd.DataFrame({'linear' : linreg.mh, 'logistic' : logreg.mh})
  meanfield = pd.DataFrame({'linear' : linreg.meanfield, 'logistic' : logreg.meanfield})
  fig, ax = plt.subplots(2, 1, figsize = (8,12))
  mh.plot(ax = ax[0], marker = '.', markersize = 10, 
          legend = {'loc' : 'upper left'})
  ax[0].set_title('Metropolis-Hastings')
  meanfield.plot(ax = ax[1], marker = '.', markersize = 10, 
                 legend = {'loc' : 'upper left'})
  ax[1].set_title('Mean-field')
  for i in (0,1):
    ax[i].legend(['Linear', 'Logistic'], loc = 'upper left')
    ax[i].set_xlabel('Input Dimensionality')
    ax[i].set_ylabel('Time per sweep')
  fig.savefig(path.join(wkdir, 'inference_time_complexity.png'))


def mk_linear_posterior(wkdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/linear_evolution'):
  '''
  Run inference for a while so we get a good posterior
  '''
 # run the model
  linreg = LinearRegression(backend = 'puma', no_ripls = 128,
                           local_mode = False) 
  linreg.build_model(2, False, None)
  linreg.simulate_data(10, 10)
  linreg.evaluate_inference(nsteps = 1, infer = '(cycle ((mh weights all 1) (mh noise all 1)) 500)')
  # store the marginal posterior on w0 as a .pkl
  marginals = {}
  marginals['w_0'] = [x[0] for x in linreg.inference_results['w'].loc[0]]
  marginals['w_1'] = [x[1] for x in linreg.inference_results['w'].loc[0]]
  marginals['sigma_2'] = linreg.inference_results['sigma_2'].loc[0]
  with open(path.join(wkdir, 'marginals.pkl'), 'wb') as f:
    pkl.dump(marginals, f, protocol = 2)

def show_evolution_linreg(outdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/linear_evolution',
                          nsweeps = 50):
  '''
  Show how the distribution of the parameters over the ripls evolves from prior
  to posterior
  '''
  # load the ground truth
  all_logscores = {}
  with open(path.join(outdir, 'marginals.pkl'), 'rb') as f:
    true_posterior = pkl.load(f)
  infers = {'mh_cycle_each' : '(cycle ((mh weights 0 1) (mh weights 1 1) (mh noise 0 1)) 5)',
            'mh_cycle_block' : '(cycle ((mh weights all 1) (mh noise all 1)) 5)',
            'mh' : '(mh default one 5)',
            'meanfield' : '(meanfield default one 10 5)'}
  for infer_label, infer in infers.items():
  # for infer_label, infer in {'map' : '(map default all 0.1 5 50)'}.items():
    figdir = path.join(outdir, infer_label)
    if not path.exists(figdir): os.mkdir(figdir)
    linreg = LinearRegression(backend = 'puma', no_ripls = 8,
                              local_mode = False)
    linreg.build_model(2, False, None)
    linreg.simulate_data(10, 10)
    linreg.evaluate_inference(nsteps = nsweeps, infer = infer)
    # collapse the logscores over the runs
    logscores = linreg.inference_results['logscore'].mean(axis = 1)
    all_logscores[infer_label] = logscores
    # get the w's and sigma squares
    red = sns.color_palette()[2]
    for i in range(0, nsweeps):
      figtitle = '{0}. Step {1}. Logscore: {2:0.1f}'.format(infer_label,
                                                           i, logscores.loc[i])
      fig, ax = plt.subplots(3, 1, figsize = [6, 14])
      # grab the data
      w_0 = linreg.inference_results['w'].loc[i].apply(lambda x: x[0])
      w_1 = linreg.inference_results['w'].loc[i].apply(lambda x: x[1])
      sigma_2 = linreg.inference_results['sigma_2'].loc[i]
      # make the plots
      # first model weight
      sns.distplot(w_0, ax = ax[0], hist = False, label = 'Program State',
                   axlabel = False)
      sns.distplot(true_posterior['w_0'], ax = ax[0], kde = True, 
                   hist = False, label = 'True Posterior', axlabel = 'w_0')
      ax[0].set_xlim([-2,6])
      ax[0].legend(loc = 'upper left')
      # second model weight
      sns.distplot(w_1, ax = ax[1], hist = False, label = 'Program State',
                   axlabel = False)
      sns.distplot(true_posterior['w_1'], ax = ax[1], kde = True, 
                   hist = False, label = 'True Posterior', axlabel = 'w_1')
      ax[1].set_xlim([-6,2])
      ax[1].legend()
      # plot the noise variance
      sigma_2 = linreg.inference_results['sigma_2'].loc[i]
      sns.distplot(sigma_2, ax = ax[2], hist = False,
                   label = 'Program State', axlabel = False)
      sns.distplot(true_posterior['sigma_2'], ax = ax[2], kde = True,
                   hist = False, label = 'True Posterior', axlabel = 'sigma_2')
      ax[2].set_xlim([0, 60])
      ax[2].legend()
      # set title, save
      fig.suptitle(figtitle)
      fig.savefig(path.join(figdir, '{0}_step_{1}'.format(infer_label, i)))
      plt.close(fig)
    # make the video
    video_name = path.join(outdir, infer_label + '.mp4')
    template_str = path.join(figdir, '{0}_step_%d.png'.format(infer_label))
    scale_correction = '"scale=trunc(iw/2)*2:trunc(ih/2)*2"'
    os.system('avconv -y -r 5 -i {0} -vf {1} {2}'.format(template_str, scale_correction, video_name))
  # plot the logscores
  all_logscores = pd.DataFrame(all_logscores)
  fig, ax = plt.subplots(1)
  all_logscores.plot(marker = '.', markersize = 10, ax = ax)
  ax.set_xlabel('Sweep')
  ax.set_ylabel('Joint log score')
  ax.set_title('Model log scores')
  fig.savefig(path.join(outdir, 'logscores.png'))

show_evolution_linreg()

def mk_logistic_posterior(wkdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/logistic_evolution'):
  '''
  Run inference for a while so we get a good posterior
  '''
 # run the model
  logreg = LogisticRegression(backend = 'puma', no_ripls = 128,
                              local_mode = False) 
  logreg.build_model(2, False, None)
  logreg.simulate_data(10, 10)
  logreg.evaluate_inference(nsteps = 1, infer = '(cycle ((mh weights all 1) (mh noise all 1)) 500)')
  # store the marginal posterior on w0 as a .pkl
  marginals = {}
  marginals['w_0'] = [x[0] for x in logreg.inference_results['w'].loc[0]]
  marginals['w_1'] = [x[1] for x in logreg.inference_results['w'].loc[0]]
  with open(path.join(wkdir, 'marginals.pkl'), 'wb') as f:
    pkl.dump(marginals, f, protocol = 2)

def show_evolution_logreg(outdir = '/Users/dwadden/code/Venturecxx/examples/dw_regression/logistic_evolution',
                          nsweeps = 50):
  '''
  Show how the distribution of the parameters over the ripls evolves from prior
  to posterior
  '''
  # load the ground truth
  with open(path.join(outdir, 'marginals.pkl'), 'rb') as f:
    true_posterior = pkl.load(f)
  infers = {'mh_cycle_each' : '(cycle ((mh weights 0 1) (mh weights 1 1) (mh noise 0 1)) 5)',
            'mh_cycle_block' : '(cycle ((mh weights all 1) (mh noise all 1)) 5)',
            'mh' : '(mh default one 5)',
            'meanfield' : '(meanfield default one 10 5)'}
  for infer_label, infer in infers.items():
    figdir = path.join(outdir, infer_label)
    if not path.exists(figdir): os.mkdir(figdir)
    logreg = LinearRegression(backend = 'puma', no_ripls = 64,
                              local_mode = False)
    logreg.build_model(2, False, None)
    logreg.simulate_data(10, 10)
    logreg.evaluate_inference(nsteps = nsweeps, infer = infer)
    # collapse the logscores over the runs
    logscores = logreg.inference_results['logscore'].mean(axis = 1)
    # get the w's and sigma squares
    red = sns.color_palette()[2]
    for i in range(0, nsweeps):
      figtitle = '{0}. Step {1}. Logscore: {2:0.1f}'.format(infer_label,
                                                           i, logscores.loc[i])
      fig, ax = plt.subplots(2, 1, figsize = [6, 10])
      # grab the data
      w_0 = logreg.inference_results['w'].loc[i].apply(lambda x: x[0])
      w_1 = logreg.inference_results['w'].loc[i].apply(lambda x: x[1])
      sigma_2 = logreg.inference_results['sigma_2'].loc[i]
      # make the plots
      # first model weight
      sns.distplot(w_0, ax = ax[0], hist = False, label = 'Program State',
                   axlabel = False)
      sns.distplot(true_posterior['w_0'], ax = ax[0], kde = True, 
                   hist = False, label = 'True Posterior', axlabel = 'w_0')
      ax[0].set_xlim([-2,6])
      ax[0].legend(loc = 'upper left')
      # second model weight
      sns.distplot(w_1, ax = ax[1], hist = False, label = 'Program State',
                   axlabel = False)
      sns.distplot(true_posterior['w_1'], ax = ax[1], kde = True, 
                   hist = False, label = 'True Posterior', axlabel = 'w_1')
      ax[1].set_xlim([-6,2])
      ax[1].legend()
      # set title, save
      fig.suptitle(figtitle)
      fig.savefig(path.join(figdir, '{0}_step_{1}'.format(infer_label, i)))
      plt.close(fig)
    # make the video
    video_name = path.join(outdir, infer_label + '.mp4')
    template_str = path.join(figdir, '{0}_step_%d.png'.format(infer_label))
    scale_correction = '"scale=trunc(iw/2)*2:trunc(ih/2)*2"'
    os.system('avconv -y -r 5 -i {0} -vf {1} {2}'.format(template_str, scale_correction, video_name))

# mk_logistic_posterior()
# show_evolution_logreg()



