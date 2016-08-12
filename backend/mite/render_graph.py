from graphviz import Digraph

import venture.mite.address as addr
from venture.mite.render import _jsonable_address

def digraph(trace, scaffold, principal_nodes=None):
  if principal_nodes is None:
    principal_nodes = set()
  dot = Digraph(name="A scaffold")
  for ad in scaffold.kernels.keys():
    name = _node_name(ad)
    def kernel_type(ad):
      ker = scaffold.kernels[ad]
      if isinstance(ker, dict) and 'type' in ker:
        return ker['type']
      else:
        return None
    if ad in principal_nodes:
      color = 'red'
    elif kernel_type(ad) == 'proposal' or kernel_type(ad) == 'propagate_lookup':
      color = 'yellow'
    elif kernel_type(ad) == 'constrained':
      color = 'blue'
    dot.node(name, label=name, fillcolor=color, style="filled")
  _add_links(dot, trace, scaffold.kernels.keys())
  return dot

def digraph_trace(trace):
  dot = Digraph(name="A trace")
  addrs = [ad for ad in trace.nodes.keys() if not isinstance(ad, addr.BuiltinAddress)]
  for ad in addrs:
    name = _node_name(ad)
    dot.node(name, label=name)
  _add_links(dot, trace, addrs)
  return dot

def _add_links(dot, trace, addrs):
  for ad in addrs:
    for child in trace.nodes[ad].children:
      if child in addrs:
        dot.edge(_node_name(ad), _node_name(child))

def _node_name(ad):
  return _jsonable_address(ad)
