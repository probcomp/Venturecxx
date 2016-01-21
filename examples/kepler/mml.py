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

from bayeslite.metamodels import sdgpm
from bdbcontrib import query
from bdbcontrib.metamodels.composer import Composer
from bdbcontrib.predictors import keplers_law
from vsgpm import VsGpm

# Load the bdb.
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
bdb = bayeslite.bayesdb_open('bdb/%s.bdb' % timestamp)

# Load satellites data.
bayeslite.bayesdb_read_csv_file(bdb, 'satellites', 'satellites.csv',
    header=True, create=True)
bdbcontrib.nullify(bdb, 'satellites', '')

# Register MML models.
composer = Composer()
composer.register_foreign_predictor(keplers_law.KeplersLaw)
bayeslite.bayesdb_register_metamodel(bdb, composer)

vsgpm = VsGpm()
bayeslite.bayesdb_register_metamodel(bdb, vsgpm)

query(bdb, '''
    CREATE GENERATOR orbital_default FOR satellites USING crosscat(
        Apogee_km NUMERICAL,
        Perigee_km NUMERICAL,
        Period_minutes NUMERICAL,
        DEPENDENT(Apogee_km, Perigee_km, Period_minutes));
    ''')

query(bdb, '''
    CREATE GENERATOR orbital_kepler FOR satellites USING composer(
        default (
            Perigee_km NUMERICAL,
            Apogee_km NUMERICAL,
        ),
        keplers_law (
            Period_minutes NUMERICAL
                GIVEN Perigee_km, Apogee_km
        )
        DEPENDENT(Apogee_km, Perigee_km)
    );''')

query(bdb, '''
    CREATE GENERATOR ven_kep FOR satellites USING vsgpm(
        columns (
            Apogee_km NUMERICAL, Perigee_km NUMERICAL,
            Period_minutes NUMERICAL),
        source (
            kepler.vnt
        ));''')

print 'INITIALIZE'
query(bdb, 'INITIALIZE 1 MODELS FOR orbital_default;')
query(bdb, 'INITIALIZE 1 MODELS FOR orbital_kepler;')
query(bdb, 'INITIALIZE 1 MODELS FOR ven_kep')

print 'ANALYZE'
query(bdb, 'ANALYZE orbital_default FOR 10 ITERATION WAIT;')
query(bdb, 'ANALYZE orbital_kepler FOR 10 ITERATION WAIT;')
query(bdb, 'ANALYZE ven_kep FOR 10 ITERATION WAIT;')

# DIFFICULT PERIOD
D1 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM orbital_default
        GIVEN Period_minutes = 7500 LIMIT 100''')

K1 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM orbital_kepler
        GIVEN Period_minutes = 7500 LIMIT 100''')

V1 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM ven_kep
        GIVEN Period_minutes = 100 LIMIT 100''')

# EASY PERIOD
D2 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM orbital_default
        GIVEN Period_minutes = 100 LIMIT 100''')

K2 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM orbital_kepler
        GIVEN Period_minutes = 100 LIMIT 100''')

V2 = query(bdb,
    '''SIMULATE Apogee_km, Perigee_km FROM ven_kep
        GIVEN Period_minutes = 100 LIMIT 100''')

# TRUE ANSWER
D3 = query(bdb,
    '''SIMULATE Apogee_km FROM orbital_default
        GIVEN Perigee_km = 17800, Period_minutes = 900 LIMIT 100''')

K3 = query(bdb,
    '''SIMULATE Apogee_km FROM orbital_kepler
        GIVEN Perigee_km = 17800, Period_minutes = 900 LIMIT 100''')

K3 = query(bdb,
    '''SIMULATE Apogee_km FROM ven_kep
        GIVEN Perigee_km = 17800, Period_minutes = 900 LIMIT 100''')
