from venture.lite.env import EnvironmentType
import venture.lite.types as t

from venture.mite.evaluator import TraceHandle
from venture.mite.state import register_trace_type
from venture.mite.state import trace_action

register_trace_type("_handle", TraceHandle, {
  "new_request": trace_action("new_request", [t.Object, t.Exp, EnvironmentType()], t.Blob),
  "value_at": trace_action("value_at", [t.Blob], t.Object),
  "free_request": trace_action("free_request", [t.Object], t.Blob),
  "restore_request": trace_action("restore_request", [t.Object], t.Blob),
})
