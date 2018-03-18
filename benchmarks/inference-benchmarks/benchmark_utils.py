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

from collections import OrderedDict
import json
import os

import numpy as np

def read_json(path):
    """Read json from file."""
    with open(path) as data_file:
        data = json.load(data_file, object_pairs_hook=OrderedDict)
    return data


def dump_json(data, path):
    """Dump json to file."""
    with open(path, 'w')\
        as outfile:
            json.dump(data, outfile, indent=4)


def mkdir(target_dir):
    """Make a directory if it does not exist."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)


def get_code_cells_from_notebook(ipynb_dict):
    """Get model, observation and inference progs from ipynb."""
    for cell in ipynb_dict['cells']:
        if cell['cell_type'] == 'code':
            if cell['source'][0].startswith('%%venturescript'):
                if cell['source'][1].strip().startswith('// MODEL'):
                    model_prog =''.join(cell['source'][2:])
                elif cell['source'][1].strip().startswith('// OBSERVATION'):
                    obs_prog =''.join(cell['source'][2:])
                elif cell['source'][1].strip().startswith('// INFERENCE'):
                    inf_prog =''.join(cell['source'][2:])
    return model_prog, obs_prog, inf_prog


def mse(target, predictions):
    """Compute mean square error."""
    error = target - predictions
    return np.mean(error**2)
