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

import math
from collections import defaultdict

import venture.ripl.utils as u
import venture.lite.value

from venture.lite.node import ConstantNode, LookupNode, OutputNode, RequestNode
from venture.lite.value import SPRef
from venture.lite.utils import logWeightsToNormalizedDirect

def find_labels_for_random_choices(trace):
  # very hacky heuristic for naming random choices.
  # scan global variables
  label_queue = []
  env = trace.globalEnv
  while env is not None:
    for name, node in env.frame.items():
      if trace.globalEnv.findSymbol(name) == node: # sanity check
        label_queue.append((node, name))
    env = env.outerEnv
  # accumulate dictionary of labels
  labels = defaultdict(list)
  for node, name in label_queue:
    node = trace.getOutermostNonReferenceNode(node)
    if name not in labels[node]:
      labels[node].append(name)
      # look for SP applications
      if isinstance(node.value, SPRef):
        families = trace.madeSPFamiliesAt(node.value.makerNode)
        for key, child_node in families.families.items():
          label_queue.append((child_node, (name, key)))
  # look up each label
  def lookup_label(node):
    if labels[node]:
      # find the shortest name
      (_, label) = min((len(str(label)), label) for label in labels[node])
      if isinstance(label, tuple):
        # SP application
        name, key = label
        if isinstance(key, RequestNode):
          # look up the arguments
          key = ", ".join(map(lookup_label, key.operandNodes))
        else:
          # super hack to prettify the string
          try:
            [value] = eval(key, vars(venture.lite.value))
            key = str(u.strip_types(value.asStackDict()))
          except Exception:
            pass
        return "{0}({1})".format(name, key)
      else:
        return label
    elif isinstance(node, ConstantNode):
      return str(u.strip_types(node.value.asStackDict()))
    elif isinstance(node, LookupNode):
      return lookup_label(node.sourceNode)
    # elif isinstance(node, OutputNode):
    #   operator_label = lookup_label(node.operatorNode)
    #   operand_labels = map(lookup_label, node.operandNodes)
    #   return [operator_label] + operand_labels
    else:
      return '<unknown value>'
  rcs = sorted((lookup_label(choice), u.strip_types(choice.value.asStackDict())) for choice in trace.rcs)
  ccs = sorted((lookup_label(choice), u.strip_types(choice.value.asStackDict())) for choice in trace.ccs)
  return rcs, ccs

class Workspace(object):
  def print_workspace(self, inferrer):
    print 'Model:'
    for directive in inferrer.engine.ripl.list_directives():
      dir_id = int(directive['directive_id'])
      dir_text = inferrer.engine.ripl._get_raw_text(dir_id)
      print "%d: %s" % (dir_id, dir_text)
    print

    model = inferrer.engine.model
    normalized_direct = logWeightsToNormalizedDirect(model.log_weights)
    for i, (trace, weight) in enumerate(zip(model.retrieve_traces(), model.log_weights)):
      print 'Trace %d:' % (i+1)
      print 'Log weight %.2f' % weight, '(normalized prob %.3g)' % normalized_direct[i]
      rcs, ccs = find_labels_for_random_choices(trace)
      for label, value in rcs:
        print label, value, '(random)'
      for label, value in ccs:
        print label, value, '(constrained)'
      print

def __venture_start__(ripl):
  workspace = Workspace()
  ripl.bind_methods_as_callbacks(workspace)
