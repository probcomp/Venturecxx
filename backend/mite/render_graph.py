from graphviz import Digraph

import venture.mite.address as addr
from venture.mite.render import _jsonable_address

def digraph(trace, scaffold, principal_nodes=None):
  if principal_nodes is None:
    principal_nodes = set()
  dot = Digraph(name="A scaffold")
  for addr in scaffold.kernels.keys():
    name = _jsonable_address(addr)
    def kernel_type(addr):
      ker = scaffold.kernels[addr]
      if isinstance(ker, dict) and 'type' in ker:
        return ker['type']
      else:
        return None
    if addr in principal_nodes:
      color = 'red'
    elif kernel_type(addr) == 'proposal' or kernel_type(addr) == 'propagate_lookup':
      color = 'yellow'
    elif kernel_type(addr) == 'constrained':
      color = 'blue'
    dot.node(name, label=name, fillcolor=color, style="filled")
  _add_links(dot, trace, scaffold.kernels.keys())
  return dot

def digraph_trace(trace):
  dot = Digraph(name="A trace")
  addrs = [a for a in trace.nodes.keys() if not isinstance(a, addr.BuiltinAddress)]
  for a in addrs:
    name = _jsonable_address(a)
    dot.node(name, label=name)
  _add_links(dot, trace, addrs)
  return dot

def _add_links(dot, trace, addrs):
  for a in addrs:
    for child in trace.nodes[a].children:
      if child in addrs:
        dot.edge(_jsonable_address(a),
                 _jsonable_address(child))
