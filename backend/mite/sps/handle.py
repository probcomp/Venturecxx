import venture.lite.types as t
from venture.lite.env import EnvironmentType

from venture.mite.evaluator import TraceHandle
from venture.mite.state import register_trace_type, trace_action

register_trace_type("_handle", TraceHandle, {
  "new_request": trace_action("new_request", [t.Object, t.Exp, EnvironmentType()], t.Blob),
  "value_at": trace_action("value_at", [t.Blob], t.Object),
})
