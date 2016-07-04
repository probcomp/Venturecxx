import numbers
from contextlib import contextmanager

from venture.exception import VentureException
from venture.lite.address import List
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.value import SPRef
import venture.lite.exp as e

from venture.untraced.node import Node, normalize

import venture.mite.address as addresses
from venture.mite.sp import VentureSP
from venture.mite.sps.compound import CompoundSP

class Evaluator(object):
  """Core of the evaluator."""

  def __init__(self, trace):
    self.trace = trace

  def eval_family(self, addr, exp, env):
    weight = 0
    value = None

    if e.isVariable(exp):
      result_node = env.findSymbol(exp)
      self.trace.register_lookup(addr, result_node)
      value = result_node.value
    elif e.isSelfEvaluating(exp):
      value = normalize(exp)
      self.trace.register_constant(addr, value)
    elif e.isQuotation(exp):
      value = normalize(e.textOfQuotation(exp))
      self.trace.register_constant(addr, value)
    elif e.isLambda(exp):
      (params, body) = e.destructLambda(exp)
      sp = CompoundSP(params, body, env)
      self.trace.register_constant(addr, sp)
      value = self.trace.register_made_sp(addr, sp)
    else:
      # SP application
      nodes = []
      for index, subexp in enumerate(exp):
        subaddr = addresses.subexpression(index, addr)
        w, v = self.eval_family(subaddr, subexp, env)
        weight += w
        nodes.append(Node(subaddr, v))

      sp_node = self.trace.deref_sp(nodes[0].value)
      args = nodes[1:]

      w, value = self.apply_sp(addr, sp_node, args)
      weight += w

      self.trace.register_application(addr, len(exp), value)
      if isinstance(value, VentureSP):
        value = self.trace.register_made_sp(addr, value)

    return (weight, value)

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = TraceHandle(self.trace, addr, sp_node.address, args)
    return (0, sp.apply(handle))

# TODO: this signature retains backward compatibility with Args for now,
# but we should remove that
from venture.lite.psp import IArgs
class TraceHandle(IArgs):
  def __init__(self, trace, app_addr, sp_addr, args):
    self.trace = trace
    self.node = app_addr
    self.sp_addr = sp_addr
    self.operandNodes = args
    self.env = None

  def operandValues(self):
    return [node.value for node in self.operandNodes]

  def py_prng(self):
    return self.trace.py_prng

  def np_prng(self):
    return self.trace.np_prng

  def request_address(self, request_id):
    return addresses.request(self.sp_addr, request_id)

  def newRequest(self, request_id, exp, env):
    # TODO return Node(value, address) so that SPs don't have to use
    # requestedValue all the time; this way the untraced interpreter
    # doesn't have to retain requests with non-repeatable request_ids.
    addr = self.request_address(request_id)
    w, _ = self.trace.eval_request(addr, exp, env)
    assert w == 0
    return request_id

  def incRequest(self, request_id):
    # TODO remove ref-counting from trace layer
    return request_id

  def hasRequest(self, request_id):
    # TODO remove ref-counting from trace layer
    # XXX for now, this breaks the trace abstraction
    addr = self.request_address(request_id)
    return addr in self.trace.results

  def requestedValue(self, request_id):
    addr = self.request_address(request_id)
    return self.trace.value_at(addr)
