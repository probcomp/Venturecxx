# code to debug Nesterov acceleration.
# didn't work in run_regression2; so, write regression with no reliance
# on the standard library to see what breaks

from venture.shortcuts import make_lite_church_prime_ripl
from matplotlib import pyplot as plt
import cPickle as pkl
import seaborn as sns
r = make_lite_church_prime_ripl()

with open('regression-evolution2/data.pkl', 'rb') as f:
  tmp = pkl.load(f)

X = tmp['X_train']
y = tmp['y_train']

###
# this works

r.clear()
r.assume('sigma_2', 0.5)
r.assume('alpha', 0.01)
r.assume('w_1', '(normal 0 (sqrt (/ sigma_2 alpha)))')
r.assume('w_2', '(normal 0 (sqrt (/ sigma_2 alpha)))')
r.assume('y', '(lambda (x_1 x_2) (normal (+ (* x_1 w_1) (* x_2 w_2)) (sqrt sigma_2)))')
for i in range(10):
  r.observe('(y 1 {0:0.2f})'.format(X.iloc[i,1]), y.iloc[i])

###
# this doesn't
r.clear()
r.load_prelude()
r.assume('sigma_2', 0.5)
r.assume('alpha', 0.01)
r.assume('w_1', '(normal 0 (sqrt (/ sigma_2 alpha)))')
r.assume('w_2', '(normal 0 (sqrt (/ sigma_2 alpha)))')
r.assume('w', '(vector w_1 w_2)')
r.assume('y', '(lambda (x) (normal (dot x w) (sqrt sigma_2)))')
for i in range(5):
  r.observe('(y (vector 1 {0:0.2f}))'.format(X.iloc[i,1]), y.iloc[i])


###

# inference command is shared for both

r.force('w_1', -5.0)
r.force('w_2', 7.0)

infer_command = '(nesterov default all 73.3 5 10)'
plotf_command = '(plotf (pts l0 l1 l2) w_1 w_2 sigma_2)'
cycle_command = '(cycle ({0} {1}) 20)'.format(plotf_command, infer_command)
res = r.infer(cycle_command)

ds = res.dataset()
fig, ax = plt.subplots(2)
ds[['w_1', 'w_2']].plot(ax = ax[0])
ax[0].set_title(infer_command)
ds['log score'].plot(ax = ax[1])