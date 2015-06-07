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

import warnings
from ..node import Node, isConstantNode, isLookupNode, isRequestNode, isOutputNode

try:
  import networkx as nx
except ImportError as e:
  succeed_to_import = False
else:
  succeed_to_import = True

def drawScaffold(trace, indexer):
  if not succeed_to_import:
    warnings.warn('Failed to import module networkx.')
  else:
    index = indexer.sampleIndex(trace)
    print "Drawing a scaffold with stats"
    index.show()
    G = traverseScaffold(trace, index)
    drawScaffoldGraph(trace, G)
    import matplotlib.pyplot as plt
    plt.show()

def traverseScaffold(trace, scaffold):
  G = nx.DiGraph()
  pnodes = scaffold.getPrincipalNodes()
  border_nodes = set([node for node_list in scaffold.border for node in node_list])
  border_nodes = border_nodes.union(scaffold.absorbing)

  # Depth first search.
  q = list(pnodes)
  G.add_nodes_from(pnodes, type='principal')
  while q:
    node = q.pop()

    # Iterate over both children and parents.
    for child in trace.childrenAt(node):
      processScaffoldNode(child, scaffold, pnodes, border_nodes, G, q)
      G.add_edge(node, child, type = 'regular')

    for parent in trace.parentsAt(node):
      processScaffoldNode(parent, scaffold, pnodes, border_nodes, G, q)
      G.add_edge(parent, node, type = 'regular')

    for parent in trace.esrParentsAt(node):
      processScaffoldNode(parent, scaffold, pnodes, border_nodes, G, q)
      G.add_edge(parent, node, type = 'regular')

  # TODO Add dotted arrow from request node to esrparent?
  return G

def processScaffoldNode(node, scaffold, pnodes, border_nodes,
                        G, q):
  if G.has_node(node):
    return

  if node in pnodes:
    type = 'principal'
  elif scaffold.isAAA(node):
    type = 'aaa'
  elif scaffold.isBrush(node):
    type = 'brush'
  elif scaffold.isResampling(node):
    # Resampling nodes in the border are drawn as DRG nodes.
    type = 'drg'
  elif node in border_nodes:
    type = 'border'
  else:
    type = 'other'
  G.add_node(node, type = type)

  if type != 'other':
    q.append(node)

def drawScaffoldGraph(trace, G, labels=None):
  color_map = {'principal': 'red',
               'drg':       'yellow',
               'border':    'blue',
               'brush':     'green',
               'aaa':       'magenta',
               'other':     'gray'}

  if labels is None:
    labels = nodeLabelDict(G.nodes(), trace)

  pos=nx.graphviz_layout(G,prog='dot')
  nx.draw_networkx(G, pos=pos, with_labels=True,
                   node_color=[color_map[data['type']] for (_,data) in G.nodes_iter(True)],
                   labels=labels)
  ## Store variables. It could be useful if further manipulation is
  ## needed from the caller.
  # trace.G = G
  # trace.labels = labels
  # trace.cm = color_map
  # trace.pos = pos

def nodeLabelDict(nodes, trace):
  # Inverse look up dict for node -> symbol from trace.globalEnv
  inv_env_dict = {}
  for (sym, env_node) in trace.globalEnv.frame.iteritems():
    assert isinstance(env_node, Node)
    assert not inv_env_dict.has_key(env_node)
    inv_env_dict[env_node] = sym

  label_dict = {}
  for node in nodes:
    if inv_env_dict.has_key(node):
      label = inv_env_dict[node]
    elif isOutputNode(node):
      label = 'O' # 'Output' #: ' + str(node.value)
    elif isRequestNode(node):
      label = 'R' # 'Request' #: ' + str(node.value)
    elif isLookupNode(node):
      label = 'L' # 'Lookup'
    elif isConstantNode(node):
      label = 'C' # 'Constant'
    else:
      label = '' # str(node.value)
    label_dict[node] = label

  return label_dict

