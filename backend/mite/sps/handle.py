from venture.lite.env import EnvironmentType
import venture.lite.types as t

from venture.mite.evaluator import TraceHandle
from venture.mite.state import register_trace_type
from venture.mite.state import trace_action

# XXX these methods have a name-clash with trace methods.
# TODO: flush trace handles entirely
# 1. give the SPs their address when they are created, so that
#    they can construct request addresses themselves
#    (obviating request_address)
# 2. have uneval_request and restore_request return/accept the weight
#    and trace fragment, so that SPs are responsible for returning
#    them in their extract/restore methods
#    (obviating the need for the trace handle to keep a reference to
#    the Regenerator object inside itself)

register_trace_type("_handle", TraceHandle, {
  "request_address": trace_action("request_address", [t.Object], t.Blob),
  "eval_request": trace_action("eval_request", [t.Blob, t.Exp, EnvironmentType()], t.Object),
  "value_at": trace_action("value_at", [t.Blob], t.Object),
  "uneval_request": trace_action("uneval_request", [t.Blob], t.Nil),
  "restore_request": trace_action("restore_request", [t.Blob], t.Object),
})
