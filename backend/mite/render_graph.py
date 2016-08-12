from graphviz import Digraph

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
  for addr in scaffold.kernels.keys():
    for child in trace.nodes[addr].children:
      if child in scaffold.kernels:
        dot.edge(_jsonable_address(addr),
                 _jsonable_address(child))
  return dot
