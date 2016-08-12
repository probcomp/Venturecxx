import venture.shortcuts as v
import venture.mite.address as addr
import venture.mite.render_graph as ren

r = v.Mite().make_ripl(seed=1)
r.set_mode("venture_script")
r.execute_program("""
define trace = run_in({
  assume coin_is_tricky ~ bernoulli(0.1);
  assume weight =
    if (coin_is_tricky) { beta(1.0, 1.0) }
    else { 0.5 };
  observe bernoulli(weight) = true;
  split_trace()
}, graph_trace());""")
trace = r.evaluate("trace")

def render(target, name, view):
    dot = ren.digraph(trace, trace.single_site_subproblem(target),
                      principal_nodes=set([target]))
    dot.format = 'png'
    dot.render(name, directory="figures", view=view)

def render_trace(view):
    dot = ren.digraph_trace(trace)
    dot.format = 'png'
    dot.render("trace", directory="figures", view=view)

# The minimal scaffold around the bernoulli choice
target1 = addr.directive(1)
render(target1, "bernoulli", view=False)

# The minimal scaffold around the beta choice
# Doesn't work because single_site_scaffold doesn't work on nodes that
# were created by requests.
# target2 = addr.request(addr.subexpression(addr.subexpression(addr.directive(2), 0), 2),
#                        addr.directive(2))
# render(target2, "beta", view=True)

# The whole trace
render_trace(view=False)
