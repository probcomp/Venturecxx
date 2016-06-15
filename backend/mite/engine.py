from venture.engine import engine
from venture.lite.value import VentureValue, SPRef
from venture.lite.types import ExpressionType
from venture.mite.traces import BlankTrace

class Engine(engine.Engine):
  def new_model(self, backend=None):
    return BlankTrace(self._py_rng.randint(1, 2**31 - 1))

  def init_inference_trace(self):
    return BlankTrace(self._py_rng.randint(1, 2**31 - 1))

  def define(self, symbol, expr):
    (addr, val) = self._do_evaluate(expr)
    self.infer_trace.bind_global(symbol, addr)
    return (addr.directive_id, val)

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
