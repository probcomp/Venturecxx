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

from collections import defaultdict
from functools import wraps

import Tkinter, ttk

import venture.ripl.utils as u
import venture.lite.value

from venture.lite.node import ConstantNode, LookupNode, RequestNode, OutputNode
from venture.lite.value import SPRef
from venture.lite.utils import logWeightsToNormalizedDirect

def catchesException(f):
  @wraps(f)
  def try_f(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except Exception:
      pass

  return try_f

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
            key = str(u.strip_types(value.asStackDict(trace)))
          except Exception:
            pass
        return "{0}({1})".format(name, key)
      else:
        return label
    elif isinstance(node, ConstantNode):
      return str(u.strip_types(node.value.asStackDict(trace)))
    elif isinstance(node, LookupNode):
      return lookup_label(node.sourceNode)
    elif isinstance(node, OutputNode):
      operator_label = lookup_label(node.operatorNode)
      operand_labels = ", ".join(map(lookup_label, node.operandNodes))
      return "{0}({1})".format(operator_label, operand_labels)
    else:
      return '<unknown value>'
  rcs = sorted((lookup_label(choice), u.strip_types(choice.value.asStackDict(trace))) for choice in trace.rcs)
  ccs = sorted((lookup_label(choice), u.strip_types(choice.value.asStackDict(trace))) for choice in trace.ccs)
  return rcs, ccs

class Workspace(object):
  def __init__(self):
    self.treeview = None

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

  def draw_workspace(self, inferrer):
    directives = inferrer.engine.ripl.list_directives()
    root = Tkinter._default_root

    if not directives:
      # don't bother drawing a window, and destroy any existing one.
      if root is not None:
        root.destroy()
      return

    if root is None:
      # create a new window
      self.treeview = None
      root = Tkinter.Tk()

    if self.treeview is None:
      # destroy any existing elements in the window
      for child in root.children.values():
        child.destroy()
      # create the treeview
      self.treeview = ttk.Treeview(root, show='tree')
      self.treeview["columns"] = ['value']
      self.treeview.column('#0', width=300)
      self.treeview.column('value', width=500)
      self.treeview.tag_configure('rcs', foreground='#722')
      self.treeview.tag_configure('ccs', foreground='#227')
      self.treeview.pack()

    # clear the treeview
    self.treeview.delete(*self.treeview.get_children())

    num_columns = 1

    # modeling directives
    model_item = self.treeview.insert('', 0, 'model', text="Modeling Directives", open=True)
    for i, directive in enumerate(directives):
      dir_id = int(directive['directive_id'])
      dir_text = inferrer.engine.ripl._get_raw_text(dir_id)
      self.treeview.insert(model_item, i, text="%d:" % dir_id, values=[dir_text])
      num_columns += 1

    # traces
    model = inferrer.engine.model
    normalized_direct = logWeightsToNormalizedDirect(model.log_weights)
    for i, (trace, weight) in enumerate(zip(model.retrieve_traces(), model.log_weights)):
      trace_text = "Trace %d (weight %.2f, prob %.3g)" % (i+1, weight, normalized_direct[i])
      trace_item = self.treeview.insert('', i+1, text=trace_text, open=True)
      rcs, ccs = find_labels_for_random_choices(trace)
      # rcs_item = self.treeview.insert(trace_item, 0, text='Random Variables', open=True)
      # ccs_item = self.treeview.insert(trace_item, 1, text='Constrained Variables', open=True)
      for label, value in rcs:
        self.treeview.insert(trace_item, 'end', text=label, values=[value], tags=['rcs'])
        num_columns += 1
      for label, value in ccs:
        self.treeview.insert(trace_item, 'end', text=label, values=[value], tags=['ccs'])
        num_columns += 1
      num_columns += 1

    # set the height dynamically
    self.treeview["height"] = num_columns

def __venture_start__(ripl):
  workspace = Workspace()
  ripl.bind_methods_as_callbacks(workspace)
  ripl.bind_callback('__postcmd__', catchesException(workspace.draw_workspace))
