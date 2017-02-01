from typing import Tuple
from typing import cast

import venture.lite.value as vv 
from venture.parser.venture_script.parse import VentureScriptParser
from venture.sivm.macro_system import desugar_expression
from venture.sivm.core_sivm import _modify_expression

from venture.knight.types import Trace
from venture.knight.types import stack_dict_to_exp
from venture.knight.regen import regen
from venture.knight.sp import init_env

def top_eval(form):
  # type: (str) -> Tuple[float, vv.VentureValue]
  stack_dict = cast(object, _modify_expression(desugar_expression(VentureScriptParser.instance().parse_expression(form))))
  return regen(stack_dict_to_exp(stack_dict), init_env(), Trace(), Trace())

print top_eval("((x) -> { x })(2)") # (0, 2)
print top_eval("normal(2, 1)") # (0, x) where x ~ normal(2, 1)
print top_eval("get_current_trace()") # (0, An empty trace)
print top_eval("trace_has(get_current_trace())") # (0, False)
print top_eval("{ t = get_current_trace(); _ = trace_set(t, 5); trace_get(t) }") # (0, 5)
print top_eval("""{
  t1 = get_current_trace();
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }""") # (0, List(List(0 . x), x)) where x ~ normal(0, 1)
print top_eval("""{
  t1 = get_current_trace();
  _ = trace_set(t1, 1);
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }""") # (0, List(List(-1.41 . 1), 1))
print top_eval("""{
  t1 = get_current_trace();
  t2 = get_current_trace();
  _ = trace_set(t2, 1);
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }""") # (0, List(List(0 . 1), 1))

normal_normal_regnerator = """
(args, constraints, interventions) -> {
  mu = args[0];
  sig1 = args[1];
  sig2 = args[2];
  if (trace_has(interventions)) {
    pair(0, trace_get(interventions))
  } else { if (trace_has(subtrace(interventions, "x"))) {
    regenerate(normal, [trace_get(subtrace(interventions, "x")), sig2],
               constraints, interventions)
  } else { // interventions trace is empty
    if (trace_has(constraints) && not(trace_has(subtrace(constraints, "x")))) {
      val = trace_get(constraints);
      prec1 = 1 / (sig1 ** 2);
      prec2 = 1 / (sig2 ** 2);
      post_mu = (mu * prec1 + val * prec2) / (prec1 + prec2);
      post_prec = prec1 + prec2;
      post_sig = sqrt(1 / post_prec);
      _ = regenerate(normal, [post_mu, post_sig],
                     subtrace(constraints, "x"), subtrace(interventions, "x"));
      regenerate(normal, [mu, sqrt(sig1**2 + sig2**2)],
                 constraints, interventions)
  } else {
    pack = regenerate(normal, [mu, sig1],
                      subtrace(constraints, "x"), subtrace(interventions, "x"));
    score = first(pack);
    val = rest(pack);
    pack2 = regenerate(normal, [val, sig2], constraints, interventions);
    score2 = first(pack2);
    val2 = rest(pack2);
    pair(score + score2, val2)
  }}}
}"""

# Running a synthetic SP
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  normal_normal(0, 1, 1)
}""" % (normal_normal_regnerator,)) # (0, x) where x ~ normal(0, 2)

# Tracing a synthetic SP
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  model = () ~> { normal_normal(0, 100, 1) };
  t1 = get_current_trace();
  t2 = get_current_trace();
  _ = regenerate(model, [], t1, t2);
  list(trace_get(subtrace(subtrace(t2, "app"), "x")), trace_get(subtrace(t2, "app")))
}""" % (normal_normal_regnerator,)) # (0, List(x, y)) where x ~ normal(0, 100) and y ~ normal(x, 1)

# Constraining a synthetic SP
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  model = () ~> { normal_normal(0, 1, 1) };
  t1 = get_current_trace();
  _ = trace_set(subtrace(t1, "app"), 5);
  t2 = get_current_trace();
  res = regenerate(model, [], t1, t2);
  list(first(res), trace_get(subtrace(subtrace(t2, "app"), "x")), trace_get(subtrace(t2, "app")))
}""" % (normal_normal_regnerator,)) # (0, List(-7.52, x, 5)) where x ~ normal(2.5, 1/sqrt(2))
