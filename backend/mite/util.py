import os
import sys

def log_regen_event(*msgs):
  if 'VENTURE_DEBUG_REGEN' in os.environ:
    print >>sys.stderr, ' '.join(map(str, msgs))

def log_regen_event_at(msg, trace, addr):
  if 'VENTURE_DEBUG_REGEN' in os.environ:
    print >>sys.stderr, msg, "at", addr
    trace.print_frame(addr, sys.stderr)

def log_scaffold_event(*msgs):
  if 'VENTURE_DEBUG_SCAFFOLD' in os.environ:
    print >>sys.stderr, ' '.join([str(m) for m in msgs])

def log_scaffold_event_at(msg, trace, addr):
  if 'VENTURE_DEBUG_SCAFFOLD' in os.environ:
    print >>sys.stderr, msg, "at", addr
    trace.print_frame(addr, sys.stderr)
