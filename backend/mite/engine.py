import venture.value.dicts as v

from venture.engine import engine
from venture.lite.value import VentureValue, SPRef
from venture.lite.types import ExpressionType
from venture.mite.traces import BlankTrace, FlatTrace

class Engine(engine.Engine):
  def new_model(self, backend=None):
    return FlatTrace(self._py_rng.randint(1, 2**31 - 1))

  def init_inference_trace(self):
    return BlankTrace(self._py_rng.randint(1, 2**31 - 1))

  def define(self, symbol, expr):
    (addr, val) = self._do_evaluate(expr)
    self.infer_trace.bind_global(symbol, addr)
    return (addr.directive_id, val)

  def assume(self, symbol, expr):
    return self.run(v.app(v.sym('_assume'), v.quote(v.sym(symbol)), v.quote(expr)))

  def observe(self, expr, value):
    return self.run(v.app(v.sym('_observe'), v.quote(expr), v.quote(value)))

  def predict(self, expr):
    return self.run(v.app(v.sym('_predict'), v.quote(expr)))

  def forget(self, directive_id):
    print 'TODO: forget', directive_id
    return 0

  def run(self, action_expr):
    (addr, val) = self.evaluate(v.app(
      v.sym('run_in'), action_expr, v.blob(self.model)))
    ([result], next_model) = val['value']
    self.model = next_model['value']
    return (addr, result)

  def infer(self, action_expr):
    return self.run(action_expr)

  def evaluate(self, expr):
    (addr, val) = self._do_evaluate(expr)
    return (addr.directive_id, val)

  def _do_evaluate(self, expr):
    trace = self.infer_trace
    addr = self.infer_trace.next_base_address()
    expr = ExpressionType().asPython(VentureValue.fromStackDict(expr))
    trace.eval_request(addr, expr, trace.global_env)
    val = trace.value_at(addr)
    if isinstance(val, SPRef):
      val = trace.deref_sp(val).value
    return (addr, val.asStackDict())

  # make the stack happy
  def predictNextDirectiveId(self):
    return self.infer_trace.directive_counter + 1
