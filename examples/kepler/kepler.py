import cPickle as pickle

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import invgamma, norm

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed

def __venture_start__(ripl, *args):
    kepler_sp = deterministic_typed(satellite_period_minutes,
        [vt.NumberType(), vt.NumberType()], vt.NumberType())
    ripl.bind_foreign_sp('kepler', kepler_sp)

def satellite_period_minutes(apogee_km, perigee_km):
    """Period of satellite with specified apogee and perigee.
    Apogee and perigee are in kilometers; period is in minutes."""
    GM = 398600.4418
    EARTH_RADIUS = 6378
    a = 0.5*(abs(apogee_km) + abs(perigee_km)) + EARTH_RADIUS
    return 2 * np.pi * np.sqrt(a**3/GM) / 60.

def simulate_nig(m, V, a, b):
    # Simulate the mean and variance from NormalInverseGamma.
    sigma2 = invgamma.rvs(a, scale=b)
    mu = norm.rvs(loc=m, scale=np.sqrt(sigma2*V))
    return (mu, sigma2)

def plot_vertical_samples(samples):
    fig, ax = plt.subplots()
    for x in samples:
        ax.vlines(x, 0, .1, linewidth=1)
    ax.set_ylim([0, 1])

# Load the dataset and add an extra column.

def plot_keplerian_surface():
    satellites = pd.read_csv('resources/satellites.csv')
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

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(X, Y, Z, alpha=.2,)
    ax.scatter(A, P, T, color='red')
    # ax.set_zlim([0, 500])
    ax.set_xlabel('Apogee', fontweight='bold')
    ax.set_ylabel('Perigee', fontweight='bold')
    ax.set_zlabel('Period', fontweight='bold')

def plot_gpmcc_clustering():
    # Plot a clustering of satellites on the 2D plane.
    Zr = np.loadtxt('resources/clusters.txt', delimiter=',')
    Q = np.genfromtxt('resources/satellites.csv', delimiter=',', skip_header=1,
        missing_values='')
    clusters = [[Q[i] for i in xrange(len(Q)) if Zr[i] == j] for j in set(Zr)]
    clusters.sort(key=lambda c: len(c), reverse=True)

    # Plot the clusters.
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    colors = ['blue','red','lightgreen','yellow','maroon','black','cyan',
        'darkorchid','pink','green','turquoise']
    for i, c in enumerate(clusters):
        data = np.asarray(c)
        ax.scatter(data[:,0], data[:,1], data[:,2], color=colors[i])
    ax.set_xlabel('Apogee', fontweight='bold')
    ax.set_ylabel('Perigee [km]', fontweight='bold')
    ax.set_zlabel('Period [mins]', fontweight='bold')
    # ax.set_zlim([0,2000])
    ax.set_title('Learned Mixture', fontweight='bold')

def plot_A_given_PT():
    D3 = np.asarray(pd.read_csv('resources/AgPT/d3.csv'))
    K3 = np.asarray(pd.read_csv('resources/AgPT/k3.csv'))
    V3 = np.asarray(pd.read_csv('resources/AgPT/v3.csv'))

    fig, ax = plt.subplots()
    ax.vlines(D3[:,1], ymin=0, ymax=1, label='Default MML', color='red')
    ax.vlines(K3[:,1], ymin=1, ymax=2, label='MML+Kepler', color='blue')
    ax.vlines(V3[:,1], ymin=2, ymax=3, label='VenKep', color='green')
    ax.vlines(31200, ymin=0, ymax=5, linewidth=2, linestyle='dashed',
        label='Exact Inverse')

    ax.set_ylim([0, 5])
    ax.set_xlabel('Posterior Samples of Apogee (km)', fontweight='bold')
    ax.set_title('SIMULATE Apogee_km GIVEN Perigee_km = 17800, '
        'Period_minutes = 900 LIMIT 100', fontweight='bold')
    ax.legend(loc='upper left', framealpha=0)
    ax.grid()

def plot_AP_given_T():
    D1 = np.asarray(pd.read_csv('resources/APgT/d1.csv'))
    K1 = np.asarray(pd.read_csv('resourecs/APgT/k1.csv'))
    V1 = np.asarray(pd.read_csv('resources/APgT/v1.csv'))

    fig, ax = plt.subplots()
    ax.scatter(D1[:,1], D1[:,2], label='Default MML', color='red')
    ax.scatter(K1[:,1], K1[:,2], label='MML+Kepler', color='blue')
    ax.scatter(V1[:,1], V1[:,2], label='VenKep', color='green')
    ax.scatter(A, P, label='Real Satellites', color='orange')

    # Compute the true curve.
    X = np.linspace(ax.get_xlim()[0], ax.get_xlim()[1], 2)
    Y = 0.333*(-3*X-38268)+253843
    ax.plot(X, Y, label='Noiseless Keplerian Solutions', color='black')

    ax.set_title('SIMULATE Apogee_km, Perigee_km GIVEN Period_minutes = 7500 '
        ' LIMIT 100', fontweight='bold')
    ax.set_xlabel('Posterior Samples of Apogee (km)', fontweight='bold')
    ax.set_ylabel('Posterior Samples of Perigee (km)', fontweight='bold')
    ax.legend(loc='upper left', framealpha=0)
    ax.grid()

def plot_AT():
    satellites = pd.read_csv('resources/satellites.csv')
    satellites['Period_minutes_kepler'] = satellite_period_minutes(
        satellites['Apogee_km'], satellites['Perigee_km'])

    A = satellites['Apogee_km']
    P = satellites['Perigee_km']
    T = satellites['Period_minutes']

    # Set up matplotlib.
    matplotlib.rcParams['legend.fontsize'] = 14
    matplotlib.rcParams['axes.titlesize'] = 18
    matplotlib.rcParams['axes.labelsize'] = 18
    matplotlib.rcParams['axes.titleweight'] = 'bold'
    matplotlib.rcParams['axes.labelweight'] = 'bold'
    matplotlib.rcParams['axes.grid'] = True
    matplotlib.rcParams['xtick.labelsize'] = 16
    matplotlib.rcParams['ytick.labelsize'] = 16

    EARTH_RADIUS = 6378

    results = pickle.load(file('resources/mml-20160122-1642-results.pkl'))

    EJ = satellites
    DJ = results['orbital_default'][10000][200][3]
    KJ = pd.read_csv('resources/orbital_kepler_AT.csv')
    VJ = results['ven_kep'][10000][200][3]

    _, ax = plt.subplots()
    ax.scatter(EJ['Apogee_km'], EJ['Period_minutes'], color='blue',
        label='Empirical Satellites')
    ax.scatter(DJ['Apogee_km'], DJ['Period_minutes'], color='red',
        label='Default MML')
    ax.scatter(KJ['Apogee_km'], KJ['Period_minutes'], color='green',
        label='Default MML + Stochastic Kepler')
    ax.scatter(VJ['Apogee_km'], VJ['Period_minutes'], color='black',
        label='VenKep (MH 1000 iter)')

    #  Parameterize by eccentricity.
    apogees = np.linspace(min(EJ['Apogee_km']), max(EJ['Apogee_km']), 10000)
    for ecc in [0.0, 1.0]:
        perigees_ecc = (apogees + EARTH_RADIUS) * (1-ecc)/(1+ecc) - EARTH_RADIUS
        periods_ecc = satellite_period_minutes(apogees, perigees_ecc)
        label = None
        if ecc == 0:
            label = 'Theoretical [ecc {:1.1f} to {:1.1f}]'.format(0,1)
        ax.plot(apogees, periods_ecc, color='purple', linestyle='dashed',
            label=label)

    ax.set_title('SIMULATE Apogee_km, Period_minutes LIMIT 100')
    ax.set_xlabel('Apogee [km]')
    ax.set_ylabel('Period [Minutes]')
    ax.set_xlim([-200, 48000])
    ax.set_ylim([-20, 1700])
    ax.legend(loc='best', framealpha=0)
    ax.grid()

def plotter_venkep_analysis():
    import cPickle as pickle

    # Load the VenKep data for block_mh.
    results = pickle.load(file('mml-results-20160122-1642/results.pkl'))
    iter_slice = 6800
    sample_slice = 20
    # Easy query.
    query = 1
    sample_ckpts = sorted(list(results['ven_kep'][iter_slice].keys()))
    iter_ckpts = sorted(list(results['ven_kep'].keys()))

    ven_kep_data = np.zeros((len(iter_ckpts), 100))
    lw_data = np.zeros((len(iter_ckpts), 100))

    for i,s in enumerate(iter_ckpts):
        # Compute ven_kep implied period.
        ven_kep = np.asarray(results['ven_kep'][s][sample_slice][query])
        ven_kep_data[i,:] = satellite_period_minutes(ven_kep[:,0], ven_kep[:,1])

        # Compute ven_kep implied period.
        lw = np.asarray(results['orbital_kepler'][s][sample_slice][query])
        lw_data[i,:] = satellite_period_minutes(lw[:,0], lw[:,1])

    fig, ax = plt.subplots()
    ax.plot(iter_ckpts, np.median(ven_kep_data, axis=1),
        color='blue')
    ax.fill_between(iter_ckpts, np.min(ven_kep_data, axis=1),
        np.max(ven_kep_data, axis=1),
        color='blue', alpha=.4)

    ax.plot(iter_ckpts, np.median(lw_data, axis=1),
        color='green')
    ax.fill_between(iter_ckpts, np.min(lw_data, axis=1),
        np.max(lw_data, axis=1),
        color='green', alpha=.4)
