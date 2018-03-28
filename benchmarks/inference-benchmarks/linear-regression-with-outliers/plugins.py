# Copyright (c) 2013-2018 MIT Probabilistic Computing Project.
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

import numpy as np

import venture.lite.types as vt
import venture.lite.value as vv
from venture.lite.sp_help import deterministic_typed

def generate_valid_symbol(index):
    return 'valid_symbol_%d' % (index,)

def __venture_start__(ripl):

    def shuffle(array):
        # Because of venture issue 306, I can't get Venture randseed directly
        # but I want shuffle to be deterministic nevertheless.
        np.random.seed(1)
        new_array = array # It seems that I have to do this, otherwise the array
        # is not mutable.
        np.random.shuffle(new_array)
        return new_array

    ripl.bind_foreign_inference_sp(
        'shuffle',
        deterministic_typed(
            shuffle,
            [vt.ArrayUnboxedType(vt.NumberType())],
            vt.ArrayUnboxedType(vt.NumberType()),
            min_req_args=1
        )
    )
    ripl.bind_foreign_inference_sp(
        'number_to_symbol',
        deterministic_typed(
            generate_valid_symbol,
            [vt.NumberType()],
            vt.SymbolType(),
            min_req_args=1
        )
    )
