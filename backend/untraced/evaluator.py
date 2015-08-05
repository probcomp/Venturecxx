# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from ..lite import exp as e
from ..lite.exception import VentureError
from venture.exception import VentureException
from ..lite.inference_sps import VentureNestedRiplMethodError # TODO Ugh.
from ..lite import value as vv

from ..lite.sp import VentureSPRecord
from ..lite.psp import PSP

import node

# We still have a notion of nodes.  A node is a thing that knows its
# address, and its value if it has one.

def eval(address, exp, env):
  # The exact parallel to venture.lite.regen.eval would be to return a
  # Node, but since the address will always be the input address,
  # might as well just return the value.
  if e.isVariable(exp):
    try:
      value = env.findSymbol(exp).value
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), None, info[2]
    return value
  elif e.isSelfEvaluating(exp): return node.normalize(exp)
  elif e.isQuotation(exp): return node.normalize(e.textOfQuotation(exp))
  else:
    nodes = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      v = eval(addr,subexp,env)
      nodes.append(node.Node(addr, v))

    try:
      val = apply(address, nodes, env)
    except VentureNestedRiplMethodError as err:
      # This is a hack to allow errors raised by inference SP actions
      # that are ripl actions to blame the address of the maker of the
      # action rather than the current address, which is the
      # application of that action (which is where the mistake is
      # detected).
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=err.addr, cause=err), None, info[2]
    except VentureException:
      raise # Avoid rewrapping with the below
    except Exception as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
    return val

def apply(address, nodes, env):
  spr = nodes[0].value
  if not isinstance(spr, VentureSPRecord):
    raise VentureException("evaluation", "Cannot apply a non-procedure", address=address)
  req_args = RequestArgs(address, nodes[1:], env)
  requests = applyPSP(spr.sp.requestPSP, req_args)
  req_nodes = [evalRequest(req_args, spr, r) for r in requests.esrs]
  assert not requests.lsrs, "The untraced evaluator does not yet support LSRs."
  return applyPSP(spr.sp.outputPSP, OutputArgs(address, nodes[1:], env, req_nodes, requests))

class RequestArgs(object):
  "A package containing all the evaluation context information that a RequestPSP might need, parallel to venture.lite.node.Args"
  def __init__(self, address, nodes, env):
    self.node = node.Node(address)
    self.operandNodes = nodes
    self.env = env
    # TODO Theoretically need spaux and madeSPAux fields

  def operandValues(self):
    ans = [n.value for n in self.operandNodes]
    for v in ans:
      assert v is None or isinstance(v, vv.VentureValue)
    return ans

class OutputArgs(RequestArgs):
  "A package containing all the evaluation context information that an OutputPSP might need, parallel to venture.lite.node.Args"
  def __init__(self, address, inputs, env, esr_nodes, requests):
    super(OutputArgs, self).__init__(address, inputs, env)
    self.esr_nodes = esr_nodes
    self.requests = requests # This field is used by "fix" for getting the environment to modify

  def esrNodes(self): return self.esr_nodes
  def esrValues(self): return [n.value for n in self.esr_nodes]
  def requestValue(self): return self.requests

def applyPSP(psp, args):
  assert isinstance(psp, PSP)
  val = psp.simulate(args)
  psp.incorporate(val, args)
  return val

def evalRequest(req_args, spr, r):
  families = spr.spFamilies
  if families.containsFamily(r.id):
    return families.getFamily(r.id)
  else:
    new_addr = req_args.node.address.request(r.addr)
    ans = node.Node(new_addr, eval(new_addr, r.exp, r.env))
    if nonRepeatableRequestID(req_args, r.id):
      pass
    else:
      families.registerFamily(r.id, ans)
    return ans

def nonRepeatableRequestID(req_args, id):
  # Conservatively detect patterns or request ids indicating intention
  # not to collide, so they do not need to be stored.
  return id == req_args.node or (isinstance(id, tuple) and id[0] == req_args.node)
