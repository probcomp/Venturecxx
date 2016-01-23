from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

import bayeslite
import bdbcontrib

from bdbcontrib.metamodels.composer import Composer
from bdbcontrib.predictors import keplers_law
from bdbcontrib.predictors import random_forest
from bdbcontrib.predictors import multiple_regression

create = False
if create:
    # Load the bdb.
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    bdb = bayeslite.bayesdb_open('bdb/%s.bdb' % timestamp)

    # Load satellites data.
    bayeslite.bayesdb_read_csv_file(bdb, 'satellites',
        'resources/satellites_full.csv', header=True, create=True)
    bdbcontrib.nullify(bdb, 'satellites', '')

    # Register MML models.
    composer = Composer()
    composer.register_foreign_predictor(keplers_law.KeplersLaw)
    composer.register_foreign_predictor(random_forest.RandomForest)
    composer.register_foreign_predictor(multiple_regression.MultipleRegression)
    bayeslite.bayesdb_register_metamodel(bdb, composer)

def create_initialize_analyze():
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
    bdb.execute('INITIALIZE 1 MODEL FOR t12;')
    print 'Analyz'
    bdb.execute('ANALYZE t12 FOR 1500 ITERATION WAIT;')

def plot_T_given_CO():
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
