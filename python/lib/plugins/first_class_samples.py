# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from venture.engine.inference import Dataset
import venture.lite.types as t
import venture.lite.value as vv
from venture.lite.sp_help import deterministic_typed

def array_from_dataset(d):
    [ind_name] = d.ind_names
    yss = d.data[ind_name]
    return map(vv.VentureValue.fromStackDict, yss)

SampleDictType = t.Dict(t.String, t.List(t.Exp))

def dict_from_dataset(dataset):
    if not isinstance(dataset, Dataset):
        dataset = dataset.getForeignBlob()
    result = dict()
    for ind_name in dataset.ind_names:
        result[ind_name] = map(vv.VentureValue.fromStackDict,
                               dataset.data[ind_name])
    return result

def __venture_start__(ripl):
    array_from_dataset_sp = deterministic_typed(array_from_dataset,
        [t.ForeignBlobType()],
        t.ArrayType())
    ripl.bind_foreign_inference_sp('array_from_dataset', array_from_dataset_sp)
    dict_from_dataset_sp = deterministic_typed(dict_from_dataset,
        [t.ForeignBlobType()], SampleDictType)
    ripl.bind_foreign_inference_sp('dict_from_dataset', dict_from_dataset_sp)
