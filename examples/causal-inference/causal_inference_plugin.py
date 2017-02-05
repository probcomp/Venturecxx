import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import in_backend
from venture.test.config import on_inf_prim
from venture.test.stats import statisticalTest
from venture.test.stats import stochasticTest
import venture.lite.value as v
import venture.lite.types as t
from venture.lite.sp import SPType
from venture.lite.psp import RandomPSP
from venture.lite.sp_help import typed_nr
from venture.lite.sp_help import deterministic_typed
import numpy as np

from pgmpy.models import BayesianModel

from venture.lite.causal_inference import MakerBDBPopulationOutputPSP 
from venture.lite.causal_inference import dag_to_dot_notation
from venture.lite.causal_inference import get_cmi_queries

def plot_posterior_dags(list_dags):
    df = pd.DataFrame({"DAG":list_dags})
    df["DAG"] = df["DAG"].replace({"":"no edge"})
    df["DAG"].value_counts("DAG").plot(kind="bar")
    plt.xlabel("DAG")
    plt.ylabel("Probability of DAG")

def __venture_start__(ripl):
    ripl.bind_foreign_inference_sp("plot_posterior_dags",
            deterministic_typed(plot_posterior_dags,
                [ 
                t.ArrayUnboxedType(t.StringType()), 
                ],
                t.NilType(),
                min_req_args=1)
            )
    ripl.bind_foreign_sp("pop",
            deterministic_typed(lambda l,i: [v.VentureNumber(l.pop(i)), 
                v.VentureArray([v.VentureNumber(item) for item in l])],
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.IntegerType(),
                ],
                t.ArrayUnboxedType(t.AnyType(), t.ArrayType()),
                min_req_args=2)
            )
    ripl.bind_foreign_sp("make_observation_function", typed_nr(MakerBDBPopulationOutputPSP(),
        [
            t.StringType(),
            t.StringType(),
            t.StringType(),
            t.ArrayUnboxedType(t.StringType()),
            t.ArrayUnboxedType(t.StringType()),
        ],
        SPType([], t.BoolType())))
    ripl.bind_foreign_sp("dag_to_dot_notation",
            deterministic_typed(dag_to_dot_notation,
                [ 
                t.ArrayUnboxedType(t.ArrayUnboxedType(t.BoolType())),
                t.ArrayUnboxedType(t.StringType())
                ],
                t.StringType(),
                min_req_args=1)
            )
    ripl.bind_foreign_inference_sp("get_cmi_queries",
            deterministic_typed(get_cmi_queries,
                [ 
                t.ArrayUnboxedType(t.StringType()),
                t.StringType(),
                ],
                t.ArrayUnboxedType(t.StringType()),
                min_req_args=1)
            )
