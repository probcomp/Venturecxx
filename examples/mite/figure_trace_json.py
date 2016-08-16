import venture.shortcuts as v
import venture.mite.render as ren

r = v.Mite().make_ripl()
r.set_mode("venture_script")
r.execute_program("""
define trace = run_in({
  assume coin_is_tricky ~ bernoulli(0.1);
  assume weight =
    if (coin_is_tricky) { beta(1.0, 1.0) }
    else { 0.5 };
  observe bernoulli(weight) = true;
  clone_trace()
}, graph_trace());""")
print ren.json(r.evaluate("trace"))
