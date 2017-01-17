from venture.lite import types as t
from venture.lite import value as v
from venture.lite.sp_help import deterministic_typed

def make_plots(results):
    print results

make_plots_sp = deterministic_typed(make_plots, [t.Object], t.Nil)

def __venture_start__(ripl):
    ripl.bind_foreign_inference_sp("make_plots", make_plots_sp)
