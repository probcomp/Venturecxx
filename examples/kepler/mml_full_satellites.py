# Copyright (c) 2013-2016 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

import bayeslite
import bdbcontrib


from bdbcontrib.bql_utils import query
from bdbcontrib.metamodels.composer import Composer
from bdbcontrib.predictors import keplers_law
from bdbcontrib.predictors import multiple_regression
from bdbcontrib.predictors import random_forest

def create_bdb():
    # Load the bdb.
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    bdb = bayeslite.bayesdb_open('bdb/%s.bdb' % timestamp)

    # Load satellites data.
    bayeslite.bayesdb_read_csv_file(bdb, 'satellites',
        'resources/satellites_all.csv', header=True, create=True)
    bdbcontrib.nullify(bdb, 'satellites', 'NaN')
    return bdb

def retrieve_bdb(filename):
    # Register MML models.
    bdb = bayeslite.bayesdb_open(filename)
    composer = Composer()
    composer.register_foreign_predictor(keplers_law.KeplersLaw)
    composer.register_foreign_predictor(random_forest.RandomForest)
    composer.register_foreign_predictor(multiple_regression.MultipleRegression)
    bayeslite.bayesdb_register_metamodel(bdb, composer)
    return bdb

def create_initialize_analyze(bdb):
    # Create default gpm.
    bdb.execute('''
        CREATE GENERATOR t11 FOR satellites USING crosscat(
            GUESS(*));''')
    bdb.execute('INITIALIZE 64 MODELS FOR t11;')
    bdb.execute('ANALYZE t11 FOR 200 ITERATION WAIT;')
    # Create the GPMs.
    bdb.execute('''
        CREATE GENERATOR t12 FOR satellites USING composer(
            default (
                Country_of_Operator CATEGORICAL, Operator_Owner CATEGORICAL,
                Users CATEGORICAL, Purpose CATEGORICAL,
                Type_of_Orbit CATEGORICAL, Perigee_km NUMERICAL,
                Apogee_km NUMERICAL, Eccentricity NUMERICAL,
                Launch_Mass_kg NUMERICAL, Dry_Mass_kg NUMERICAL,
                Power_watts NUMERICAL, Date_of_Launch NUMERICAL,
                Contractor CATEGORICAL,
                Country_of_Contractor CATEGORICAL, Launch_Site CATEGORICAL,
                Launch_Vehicle CATEGORICAL,
                Source_Used_for_Orbital_Data CATEGORICAL,
                longitude_radians_of_geo NUMERICAL,
                Inclination_radians NUMERICAL,
            ),
            random_forest (
                Class_of_orbit CATEGORICAL
                    GIVEN Apogee_km, Perigee_km,
                        Eccentricity, Period_minutes, Launch_Mass_kg,
                        Power_watts, Anticipated_Lifetime, Type_of_Orbit
            ),
            keplers_law (
                Period_minutes NUMERICAL
                    GIVEN Perigee_km, Apogee_km
            ),
            multiple_regression (
                Anticipated_Lifetime NUMERICAL
                    GIVEN Dry_Mass_kg, Power_watts, Launch_Mass_kg, Contractor
            ),
            DEPENDENT(Apogee_km, Perigee_km, Eccentricity),
        );''')

    print 'Init'
    bdb.execute('INITIALIZE 64 MODELS FOR t12;')
    print 'Analyz'
    bdb.execute('ANALYZE t12 FOR 150 ITERATION WAIT;')


def plot_T_given_CO(bdb):
    create = False
    if create:
        leo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "LEO"''').fetchall()
        geo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "GEO"''').fetchall()
        meo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "MEO"''').fetchall()
        elliptical = bdb.execute('''SELECT Period_minutes FROM satellites
            WHERE Class_of_orbit = Elliptical''').fetchall()
        samples_leo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "LEO" LIMIT 100;''').fetchall()
        samples_geo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "GEO" LIMIT 100;''').fetchall()
        samples_meo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "MEO" LIMIT 100;''').fetchall()
        samples_elliptical = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "Elliptical" LIMIT 100;''').fetchall()
    else:
        leo = np.loadtxt('resources/TgCO/leo')
        geo = np.loadtxt('resources/TgCO/geo')
        meo = np.loadtxt('resources/TgCO/meo')
        elliptical = np.loadtxt('resources/TgCO/elliptical')
        samples_leo = list(np.loadtxt('resources/TgCO/samples_leo'))
        samples_geo = list(np.loadtxt('resources/TgCO/samples_geo'))
        samples_meo = list(np.loadtxt('resources/TgCO/samples_meo'))
        samples_elliptical = list(np.loadtxt('resources/TgCO/samples_elliptical'))

    fig, ax = plt.subplots(2,1)

    ax[0].hlines(leo, xmin=0, xmax=1, label='LEO', color='blue')
    ax[0].hlines(geo, xmin=1, xmax=2, label='MEO', color='red')
    ax[0].hlines(meo, xmin=2, xmax=3, label='GEO', color='green')
    ax[0].hlines(elliptical, xmin=3, xmax=4, label='Elliptical', color='black')
    ax[0].set_title('SELECT Period_minutes, Class_of_orbit FROM'
        ' satellites ORDER BY Class_of_orbit''', fontweight='bold',size=16)

    ax[1].hlines(samples_leo[:10]+samples_leo[-10:], xmin=0, xmax=1,
        label='LEO', color='blue')
    ax[1].hlines(samples_meo[:10]+samples_meo[-10:],
        xmin=1, xmax=2, label='MEO', color='red')
    ax[1].hlines(samples_geo[60:70] + samples_geo[80:90],
        xmin=2, xmax=3, label='GEO', color='green')
    ax[1].hlines(samples_elliptical[:10]+samples_elliptical[-10:],
        xmin=3, xmax=4, label='Elliptical', color='black')
    ax[1].set_title('''
        SIMULATE Period_minutes FROM satellites GIVEN Class_of_orbit''',
        fontweight='bold', size=16)

    for a in ax:
        a.set_xlim([0,4])
        a.set_xlim([0,4])
        a.set_ylim([0,4000])
        a.set_ylim([0,4000])
        a.set_xticks([0.5, 1.5, 2.5, 3.5])
        a.set_xticklabels(['LEO','MEO','GEO','Elliptical'])
        a.set_ylabel('Period (minutes)', fontweight='bold', size=16)
        a.grid()
        a.grid()


def plot_period_perigee_given_purpose(bdb):
    # bdb.execute("""
    #     CREATE TABLE period_perigee_given_purpose_t11 AS
    #         SIMULATE perigee_km, period_minutes FROM t11
    #         GIVEN purpose = 'Communications' LIMIT 1000;""")

    # bdb.execute("""
    #     CREATE TABLE period_perigee_given_purpose_t12 AS
    #         SIMULATE perigee_km, period_minutes FROM t12
    #         GIVEN purpose = 'Communications' LIMIT 100;""")

    t11 = np.asarray(bdb.execute(
        'SELECT * FROM period_perigee_given_purpose_t11 LIMIT 75;').fetchall())
    t12 = np.asarray(bdb.execute(
        'SELECT * FROM period_perigee_given_purpose_t12 LIMIT 75;').fetchall())

    fig, ax = plt.subplots(nrows=1, ncols=2)
    fig.suptitle('SIMULATE period_minutes, perigee_km '
        'GIVEN purpose = \'Communications\'', fontweight='bold', fontsize=18)

    ax[0].scatter(t11[:,0], t11[:,1], color='r', label='Crosscat',
        s=8)
    ax[0].set_xlim(-1000, 48000)
    ax[0].set_ylim(-100, 1800)

    ax[1].scatter(t12[:,0], t12[:,1], color='g', label='Crosscat + Kepler',
        s=8)
    ax[1].set_xlim(*ax[0].get_xlim())
    ax[1].set_ylim(*ax[0].get_ylim())

    for a in ax:
        a.grid()
        a.legend(framealpha=0, loc='upper left')
        a.set_xlabel('Perigee [km]', fontweight='bold', fontsize=12)
        a.set_ylabel('Period [mins]', fontweight='bold', fontsize=12)

bdb = retrieve_bdb('bdb/20160513-122941.bdb')
plot_period_perigee_given_purpose(bdb)
