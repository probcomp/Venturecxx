import argparse

from typing import Tuple # Pylint doesn't understand type comments pylint: disable=unused-import
from typing import cast

from venture.parser.venture_script.parse import VentureScriptParser
from venture.sivm.core_sivm import _modify_expression
from venture.sivm.macro_system import desugar_expression
import venture.lite.value as vv # Pylint doesn't understand type comments pylint: disable=unused-import

from venture.knight.regen import regen
from venture.knight.sp import init_env
from venture.knight.types import Trace
from venture.knight.types import stack_dict_to_exp

def top_eval(form):
  # type: (str) -> Tuple[float, vv.VentureValue]
  stack_dict = cast(object, _modify_expression(desugar_expression(VentureScriptParser.instance().parse_expression(form))))
  return regen(stack_dict_to_exp(stack_dict), init_env(), Trace(), Trace())

def doit(args):
  # type: (argparse.Namespace) -> None
  if args.eval:
    for exp in args.eval:
      print top_eval(exp)

def main():
  # type: () -> None
  parser = argparse.ArgumentParser()
  parser.add_argument('-e', '--eval', action='append', help="execute the given expression")
  parser.add_argument('-f', '--file', action='append', help="execute the given file")
  args = parser.parse_args()
  doit(args)

if __name__ == '__main__':
  main()

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
(args, target, mechanism) -> {
  mu = args[0];
  sig1 = args[1];
  sig2 = args[2];
  if (trace_has(mechanism)) {
    pair(0, trace_get(mechanism))
  } else { if (trace_has(subtrace(mechanism, "x"))) {
    regenerate(normal, [trace_get(subtrace(mechanism, "x")), sig2],
               target, mechanism)
  } else { // mechanism trace is empty
    if (trace_has(target) && not(trace_has(subtrace(target, "x")))) {
      val = trace_get(target);
      prec1 = 1 / (sig1 ** 2);
      prec2 = 1 / (sig2 ** 2);
      post_mu = (mu * prec1 + val * prec2) / (prec1 + prec2);
      post_prec = prec1 + prec2;
      post_sig = sqrt(1 / post_prec);
      post_sample ~ normal(post_mu, post_sig);
      _ = trace_set(subtrace(mechanism, "x"), post_sample);
      regenerate(normal, [mu, sqrt(sig1**2 + sig2**2)],
                 target, mechanism)
  } else {
    pack = regenerate(normal, [mu, sig1],
                      subtrace(target, "x"), subtrace(mechanism, "x"));
    score = first(pack);
    val = rest(pack);
    pack2 = regenerate(normal, [val, sig2], target, mechanism);
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

# Test generic regenerator_of
print top_eval("""{
  t1 = get_current_trace();
  t2 = get_current_trace();
  _ = trace_set(t2, 1);
  res = regenerate(sp(regenerator_of(normal)), [0, 1], t1, t2);
  list(res, trace_get(t2)) }""") # (0, List(List(0 . 1), 1))

# Test tracing a mechanism
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  t1 = get_current_trace();
  t2 = get_current_trace();
  t3 = get_current_trace();
  t4 = get_current_trace();
  _ = regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(trace_get(subtrace(t2, "x")), t4)
}""" % (normal_normal_regnerator,)) # (0, List(x, a trace)) where x ~ normal(0, 1)

# Test another trace of a mechanism
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  t1 = get_current_trace();
  t2 = get_current_trace();
  _ = trace_set(t1, 5);
  t3 = get_current_trace();
  t4 = get_current_trace();
  res = regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(res, trace_get(subtrace(t2, "x")), t4)
}""" % (normal_normal_regnerator,)) # (0, List(List(0, -7.52 . 5), x, a trace)) where x ~ normal(2.5, 1/sqrt(2))

# Test intervening on a traced mechanism
# Compare the test case "constraining a synthetic SP"
print top_eval("""{
  regenerator = %s;
  normal_normal = sp(regenerator);
  t1 = get_current_trace();
  _ = trace_set(t1, 5);
  t2 = get_current_trace();
  t3 = get_current_trace();
  t4 = get_current_trace();
  _ = trace_set(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(subtrace(t4, "app"), "app"), "app"), "app"), "app"), "app"), "app"), "app"), "app"), "app"), "app"), "app"), 1), "app"), 7);
  res = regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(res, trace_get(subtrace(t2, "x")), t4)
}""" % (normal_normal_regnerator,)) # (0, List(List(0, -7.52 . 5), 7, a trace))
