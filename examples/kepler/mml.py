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

timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
bdb = bayeslite.bayesdb_open('bdb/%s.bdb' % timestamp)


bayeslite.bayesdb_read_csv_file(bdb, 'satellites', 'satellites.csv',
    header=True, create=True)
bdbcontrib.nullify(bdb, 'satellites', '')

composer = Composer()
composer.register_foreign_predictor(keplers_law.KeplersLaw)
bayeslite.bayesdb_register_metamodel(bdb, composer)

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

query(bdb, 'INITIALIZE 8 MODELS FOR orbital_default;')
query(bdb, 'INITIALIZE 8 MODELS FOR orbital_kepler;')

query(bdb, 'ANALYZE orbital_default FOR 10 ITERATION WAIT;')
query(bdb, 'ANALYZE orbital_kepler FOR 10 ITERATION WAIT;')
