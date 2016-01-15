from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gpmcc.dists.normal import Normal

satellites = pd.read_csv('satellites.csv')

def satellite_period_minutes(apogee_km, perigee_km):
    """Period of satellite with specified apogee and perigee.
    Apogee and perigee are in kilometers; period is in minutes."""
    GM = 398600.4418
    EARTH_RADIUS = 6378
    a = 0.5*(abs(apogee_km) + abs(perigee_km)) + EARTH_RADIUS
    return 2 * np.pi * np.sqrt(a**3/GM) / 60.

A = satellites['Apogee_km']
P = satellites['Perigee_km']

satellites['Period_minutes_kepler'] = satellite_period_minutes(A, P)
T = satellites['Period_minutes']
TT = satellites['Period_minutes_kepler']

x, y = np.linspace(0, 1000, 100), np.linspace(0, 1000, 100)
X, Y = np.meshgrid(x, y)
X, Y = X[Y<X], Y[Y<X]
Z = satellite_period_minutes(X, Y)

plot = False
if plot:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(X, Y, Z, alpha=.2,)
    ax.scatter(A, P, T, color='red')
    ax.set_zlim([0, 500])
    ax.set_xlabel('Apogee', fontweight='bold')
    ax.set_ylabel('Perigee', fontweight='bold')
    ax.set_zlabel('Period', fontweight='bold')

