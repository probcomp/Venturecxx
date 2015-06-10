# Copyright (c) 2015 MIT Probabilistic Computing Project.
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
  assert isinstance(spr, VentureSPRecord)
  requests = applyPSP(spr.sp.requestPSP, RequestArgs(address, nodes[1:], env))
  req_nodes = [evalRequest(address, r) for r in requests.esrs]
  # TODO Do I need to do anything about LSRs?
  return applyPSP(spr.sp.outputPSP, OutputArgs(address, nodes[1:], env, req_nodes))

class RequestArgs(object):
  "A package containing all the evaluation context information that a RequestPSP might need, parallel to venture.lite.node.Args"
  def __init__(self, address, nodes, env):
    self.node = node.Node(address)
    self.operandNodes = nodes
    self.operandValues = [n.value for n in nodes]
    for v in self.operandValues:
      # v could be None if this is for logDensityBound for rejection
      # sampling, which is computed from the torus.
      assert v is None or isinstance(v, vv.VentureValue)
    self.isOutput = False
    self.env = env

class OutputArgs(RequestArgs):
  "A package containing all the evaluation context information that an OutputPSP might need, parallel to venture.lite.node.Args"
  def __init__(self, address, inputs, env, esr_nodes):
    super(OutputArgs, self).__init__(address, inputs, env)
    self.isOutput = True
    self.esrNodes = esr_nodes
    self.esrValues = [n.value for n in esr_nodes]

def applyPSP(psp, args):
  assert isinstance(psp, PSP)
  val = psp.simulate(args)
  psp.incorporate(val, args)
  # At this point, Lite converts any SPRecord values to SPRefs
  return val

def evalRequest(address, r):
  # TODO Maintain mem tables by request id
  new_addr = address.request(r.addr)
  return node.Node(new_addr, eval(new_addr, r.exp, r.env))
