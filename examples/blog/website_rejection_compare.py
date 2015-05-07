import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats.distributions import poisson

def readme(path):
  return pd.read_table(path).set_index('nballs').loc[np.r_[0:21]].fillna(0)

web = readme('blog_website.txt')
web.columns = ['web']
rejection = readme('blog_rejection_posterior_n2500.txt')
rejection.columns = ['rejection']

fig, (ax1, ax2) = plt.subplots(2)
web.plot(kind = 'bar', ax = ax1, alpha = 0.5, color = 'blue')
rejection.plot(kind = 'bar', ax = ax1, alpha = 0.5, color = 'red')

prior = pd.DataFrame(poisson.pmf(np.r_[0:21], 6))
prior.columns = ['prior']
prior.plot(kind = 'bar', ax = ax2, alpha = 0.5, color = 'green')

for ax in ax1, ax2:
  ax.set_xlim([0,21])
  ax.set_ylim([0, 0.2])

fig.savefig('rejection_website_comparison.png')
