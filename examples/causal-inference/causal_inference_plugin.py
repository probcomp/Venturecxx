import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    ax = df["DAG"].value_counts("DAG").plot(kind="bar")
    ax.set_xlabel("DAG", fontsize=12)
    ax.set_ylabel("Probability of DAG", fontsize=12)
    ax.set_title("Posterior over possible DAG structures", fontsize=15)
    xlabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
    ax.set_xticklabels(xlabels, fontsize=12)
    plt.tick_params(axis='y', which='major', labelsize=12)
    plt.tick_params(axis='y', which='minor', labelsize=12)


def __venture_start__(ripl):

    sns.set_context("paper")

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
        ],
        SPType([], t.ArrayUnboxedType(t.StringType()))))
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

    ripl.execute_program("""
        assume find = (list, item) -> {find_helper(to_list(list), item, 0)};
        assume find_helper = (list, item, index) -> {
               if(list[0]==item)
                    {index}
               else
                    {find_helper(rest(list), item, index + 1)}};
     """)
