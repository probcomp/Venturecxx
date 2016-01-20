import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import invgamma, norm

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed

from gpmcc.dists.normal import Normal

def satellite_period_minutes(apogee_km, perigee_km):
    """Period of satellite with specified apogee and perigee.
    Apogee and perigee are in kilometers; period is in minutes."""
    GM = 398600.4418
    EARTH_RADIUS = 6378
    a = 0.5*(abs(apogee_km) + abs(perigee_km)) + EARTH_RADIUS
    return 2 * np.pi * np.sqrt(a**3/GM) / 60.

def simulate_params(m, V, a, b):
    # Simulate the mean and variance from NormalInverseGamma.
    # https://en.wikipedia.org/wiki/Normal-inverse-gamma_distribution#Generating_normal-inverse-gamma_random_variates
    sigma2 = invgamma.rvs(a, scale=b)
    mu = norm.rvs(loc=m, scale=np.sqrt(sigma2*V))
    return (mu, sigma2)

def plot_samples(samples):
    fig, ax = plt.subplots()
    for x in samples:
        ax.vlines(x, 0, .1, linewidth=1)
    ax.set_ylim([0, 1])

def __venture_start__(ripl, *args):
    kepler_sp = deterministic_typed(satellite_period_minutes,
        [vt.NumberType(), vt.NumberType()], vt.NumberType())
    ripl.bind_foreign_sp('kepler', kepler_sp)


# Load the dataset and add an extra column.
satellites = pd.read_csv('satellites.csv')
satellites['Period_minutes_kepler'] = satellite_period_minutes(
    satellites['Apogee_km'], satellites['Perigee_km'])

# Extract columns for reuse.
A = satellites['Apogee_km']
P = satellites['Perigee_km']
T = satellites['Period_minutes']
TT = satellites['Period_minutes_kepler']

x, y = np.linspace(0, 100000, 100), np.linspace(0, 100000, 100)
X, Y = np.meshgrid(x, y)
X, Y = X[Y<X], Y[Y<X]
Z = satellite_period_minutes(X, Y)

plot = 0
if plot:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(X, Y, Z, alpha=.2,)
    ax.scatter(A, P, T, color='red')
    ax.set_zlim([0, 500])
    ax.set_xlabel('Apogee', fontweight='bold')
    ax.set_ylabel('Perigee', fontweight='bold')
    ax.set_zlabel('Period', fontweight='bold')

# Plot a clustering of satellites on the 2D plane.
Zr = np.loadtxt('clusters.txt', delimiter=',')
Q = np.genfromtxt('satellites.csv', delimiter=',', skip_header=1,
    missing_values='')
clusters = [[Q[i] for i in xrange(len(Q)) if Zr[i] == j] for j in set(Zr)]
clusters.sort(key=lambda c: len(c), reverse=True)

# Plot the clusters.
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
colors = ['blue','red','lightgreen','yellow','maroon','black','cyan','darkorchid',
    'pink','green','turquoise']
for i,c in enumerate(clusters):
    data = np.asarray(c)
    ax.scatter(data[:,0], data[:,1], data[:,2], color=colors[i])
ax.set_xlabel('Apogee', fontweight='bold')
ax.set_ylabel('Perigee [km]', fontweight='bold')
ax.set_zlabel('Period [mins]', fontweight='bold')
# ax.set_zlim([0,2000])
ax.set_title('Learned Mixture', fontweight='bold')



