# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from collections import namedtuple
import math

from venture.lite.orderedset import OrderedFrozenSet
from venture.lite.scaffold import constructScaffold, Scaffold
from venture.lite.smap import SamplableMap
from venture.lite.sp_help import deterministic_typed
from venture.lite.wttree import PSet
import venture.lite.inference_sps as inf
import venture.lite.node as n
import venture.lite.types as t

def _is_set(thing):
  return isinstance(thing, OrderedFrozenSet) or isinstance(thing, PSet)

def _canonicalize_to_ordered_frozen_set(thing):
  if isinstance(thing, PSet):
    # Intended type canonicalization
    return OrderedFrozenSet(list(thing))
  else:
    # Defensive copy, because trace.unregisterRandomChoice may mutate
    # the underlying set
    return OrderedFrozenSet(list(thing))

# The language of possible subproblem selection phrases.  The item in
# each field is expected to be one of these, except Lookup.key,
# Edge.edge, and FetchTag.name are expected to be objects.

Intersect = namedtuple("Intersect", ["source1", "source2"])
Lookup = namedtuple("Lookup", ["key", "dictionary"])
Random1 = namedtuple("Random1", ["source"])
Edge = namedtuple("Edge", ["source", "edge"])
Extent = namedtuple("Extent", ["source"])
UnionDict = namedtuple("UnionDict", ["source"])
Union = namedtuple("Union", ["sources"])
FetchTag = namedtuple("FetchTag", ["name"])
Top = namedtuple("Top", [])
Star = namedtuple("Star", [])
MinimalSubproblem = namedtuple("MinimalSubproblem", ["source"])

EsrEdge = namedtuple("EsrEdge", ["index"])

def is_search_ast(thing):
  return (isinstance(thing, Intersect) or
          isinstance(thing, Lookup) or
          isinstance(thing, Random1) or
          isinstance(thing, Edge) or
          isinstance(thing, Extent) or
          isinstance(thing, UnionDict) or
          isinstance(thing, Union) or
          isinstance(thing, FetchTag) or
          isinstance(thing, Top) or
          isinstance(thing, MinimalSubproblem))

# TODO Not supporting ordered scaffolds (as for pgibbs) yet, though I
# guess we could, by adding an "ordered list of sets of nodes" object
# and an appropriate AST node to make one of those from a dictionary.
# But maybe pgibbs should just be written as a (horrible) inference
# program.

# TODO This is called an "Indexer" because we never renamed
# "BlockScaffoldIndexer" to anything more sensible.  The theory in the
# original nomenclature was that mixmh was "indexed" by some computed
# auxiliary variable.
class TraceSearchIndexer(object):
  def __init__(self, prog):
    # TODO Not supporting subsampling yet, because that's too old and
    # confusing, and this is too new.
    # TODO Also not supporting delta kernels, for a similar reason.
    self.prog = prog

  def sampleIndex(self, trace):
    (scaffold, _weight) = interpret(self.prog, trace)
    assert isinstance(scaffold, Scaffold)
    return scaffold

  def logDensityOfIndex(self, trace, _):
    # Two things:
    #
    # - The marginal probability of producing the same result is
    #   actually intractable, so this is computing the probability of
    #   following the same path (which may not actually yield the same
    #   result, per Issue #576 (scope membership reversibility)).
    #
    # - In cases with only one random choice, the probability of
    #   following the same path is independent of the path.  To handle
    #   the more general case, I need to change the interface of
    #   Indexers to be able to return a trace of the path they
    #   followed so it can be replayed in the new context.
    #   - Interestingly, this may also lead to a solution to #576, at
    #     least in the form of rejecting transitions that are not
    #     reversible.
    #
    # Until then, just return the weight and hope.
    (scaffold, weight) = interpret(self.prog, trace)
    assert isinstance(scaffold, Scaffold)
    return weight

# The return value of interpret is expected to be one of
# - A single node
# - An OrderedSet or OrderedFrozenSet of nodes
# - A SamplableMap from keys to nodes
# - A Scaffold
# - The Top() object (serving as a special token denoting the top of the trace)
def interpret(prog, trace):
  if isinstance(prog, Intersect):
    (s1, w1) = interpret(prog.source1, trace)
    (s2, w2) = interpret(prog.source2, trace)
    return (intersect(s1, s2), w1 + w2)
  elif isinstance(prog, Lookup):
    (d, w) = interpret(prog.dictionary, trace)
    return (d[prog.key], w)
  elif isinstance(prog, Random1):
    (thing, wt) = interpret(prog.source, trace)
    ans = sample_one(thing, trace.py_rng)
    wt2 = -1 * math.log(len(thing))
    return (ans, wt + wt2)
  elif isinstance(prog, Edge):
    (thing, wt) = interpret(prog.source, trace)
    if prog.edge in t.ForeignBlobType() and \
       (isinstance(prog.edge.datum, FetchTag) or isinstance(prog.edge.datum, Lookup)):
      (thing2, wt2) = interpret(Extent(prog.edge.datum), trace)
      return (intersect(extent(thing, trace), thing2), wt + wt2)
    elif prog.edge in t.ForeignBlobType() and \
         isinstance(prog.edge.datum, Star):
      return (extent(thing, trace), wt)
    else:
      return (follow_edge(thing, prog.edge, trace), wt)
  elif isinstance(prog, Extent):
    (thing, wt) = interpret(prog.source, trace)
    return (extent(thing, trace), wt)
  # elif isinstance(prog, UnionDict):
  elif isinstance(prog, Union):
    (sources, weights) = zip(*[interpret(source, trace) for source in prog.sources])
    return (reduce(union, sources), sum(weights))
  elif isinstance(prog, FetchTag):
    return (trace.scopes[prog.name], 0)
  elif isinstance(prog, Top):
    return (Top(), 0) # Hack: Top as a node set is also a special token, reusing the same token
  elif isinstance(prog, MinimalSubproblem):
    (nodes, wt) = interpret(prog.source, trace)
    node_set = as_set(nodes)
    assert _is_set(node_set)
    for node in node_set:
      assert isinstance(node, n.Node), node
    return (constructScaffold(trace, [_canonicalize_to_ordered_frozen_set(node_set)]), wt)
  else:
    raise Exception("Unknown trace search term %s" % (prog,))

def intersect(thing1, thing2):
  return set_fmap2(thing1, thing2, lambda nodes1, nodes2: nodes1.intersection(nodes2))

def union(thing1, thing2):
  return set_fmap2(thing1, thing2, lambda nodes1, nodes2: nodes1.union(nodes2))

def sample_one(thing, prng):
  if isinstance(thing, SamplableMap):
    return thing.sample(prng)[1]
  elif _is_set(thing):
    return prng.sample(list(thing),1)[0]
  else:
    raise Exception("Can only sample one element of a collection, not %s" % (thing,))

def follow_edge(thing, edge, trace):
  if isinstance(thing, Top):
    if edge in t.NumberType():
      did = int(edge.getNumber())
      return trace.families[did]
    else:
      raise Exception("Selecting subproblems by label is not supported")
  else:
    return set_bind(thing, follow_func(edge, trace))

def follow_func(edge, trace):
  if edge in t.NumberType():
    def doit(node):
      if n.isApplicationNode(node):
        # The subexpressions are the definite parents, accidentally in
        # the order useful for this
        return OrderedFrozenSet([trace.definiteParentsAt(node)[int(edge.getNumber())]])
      else:
        return OrderedFrozenSet([])
    return doit
  elif edge in t.SymbolType() or edge in t.StringType():
    name = edge.getSymbol()
    if name == "operator":
      return follow_func(t.NumberType().asVentureValue(0), trace)
    elif name == "source":
      def doit(node):
        if n.isLookupNode(node):
          # The definite parents are the lookup source
          return OrderedFrozenSet([trace.definiteParentsAt(node)[0]])
        else:
          return OrderedFrozenSet([])
      return doit
    elif name == "request":
      def doit(node):
        if n.isOutputNode(node):
          # The last definite parent is the request node
          return OrderedFrozenSet([trace.definiteParentsAt(node)[-1]])
        else:
          return OrderedFrozenSet([])
      return doit
    else:
      raise Exception("Unknown named edge type %s" % (name,))
  elif edge in t.ForeignBlobType() and isinstance(edge.datum, EsrEdge):
    def doit(node):
      if n.isApplicationNode(node):
        return OrderedFrozenSet([trace.esrParentsAt(node)[int(edge.datum.index)]])
      else:
        return OrderedFrozenSet([])
    return doit
  else:
    raise Exception("Unknown edge type %s" % (edge,))

def extent(thing, trace):
  if isinstance(thing, Top):
    return trace.rcs
  return set_fmap(thing, lambda nodes: trace.randomChoicesInExtent(nodes, None, None))

def as_set(thing):
  if _is_set(thing):
    return thing
  elif isinstance(thing, SamplableMap):
    ans = OrderedFrozenSet()
    for _, v in thing.iteritems():
      ans = ans.union(v)
    return ans
  else:
    return OrderedFrozenSet([thing])

def set_fmap(thing, f):
  "Lift an f :: set -> a to accept sets, single nodes (by upgrading), or dictionaries (pointwise)."
  if isinstance(thing, SamplableMap):
    ans = SamplableMap()
    for k, v in thing.iteritems():
      ans[k] = f(v)
    return ans
  elif _is_set(thing):
    return f(_canonicalize_to_ordered_frozen_set(thing))
  else:
    return f(OrderedFrozenSet([thing]))

def set_bind(thing, f):
  "Lift an f :: a -> set b to accept sets (pointwise-union) or dictionaries (pointwise pointwise-union)."
  if isinstance(thing, SamplableMap):
    ans = SamplableMap()
    for k, v in thing.iteritems():
      ans[k] = set_bind(v, f)
    return ans
  elif _is_set(thing):
    return OrderedFrozenSet([]).union(*[f(v) for v in thing])
  else:
    return f(thing)

def set_fmap2(thing1, thing2, f):
  """Lift a binary f :: set, set -> a to accept sets, single nodes (by
upgrading), or dictionaries (pointwise, cross product if two)."""
  if isinstance(thing1, SamplableMap) and isinstance(thing2, SamplableMap):
    ans = SamplableMap()
    for k1,v1 in thing1.iteritems():
      for k2,v2 in thing2.iteritems():
        ans[(k1, k2)] = f(v1, v2)
    return ans
  elif isinstance(thing2, SamplableMap):
    return set_fmap(thing2, lambda nodes: f(as_set(thing1), nodes))
  else:
    return set_fmap(thing1, lambda nodes: f(nodes, as_set(thing2)))

inf.registerBuiltinInferenceSP("by_intersection",
    deterministic_typed(Intersect, [t.ForeignBlobType(), t.ForeignBlobType()], t.ForeignBlobType(), descr="""
Intersect the selected choices.
"""))

inf.registerBuiltinInferenceSP("by_tag", \
    deterministic_typed(FetchTag, [t.AnyType("<tag>")], t.ForeignBlobType(), descr="""
Select the choices tagged by the given tag.

They remain keyed by their values, so that `random_singleton` will
pick all the choices given by a random tag value, rather than a single
choice at random from all choices under that tag.
"""))

def by_tag_value_fun(tag, val):
  return Lookup(val, FetchTag(tag))

inf.registerBuiltinInferenceSP("by_tag_value", \
    deterministic_typed(by_tag_value_fun, [t.AnyType("<tag>"), t.AnyType("<value>")], t.ForeignBlobType(), descr="""
Select the choices tagged by the given tag at the given value.
"""))

inf.registerBuiltinInferenceSP("by_walk", \
    deterministic_typed(Edge, [t.ForeignBlobType(), t.AnyType("<edge>")], t.ForeignBlobType(), descr="""
Walk along the given edge in the dependency graph pointwise.

Possible edges are
- `operator`, for the operator position of an expression
- `source`, for the expression a variable is bound to
- `request`, for the request node corresponding to a procedure application
- <an integer>, for that index subexpression of an expression
- <a tag search expression>, for choices in the dynamic extent of a node
  that were given in that tag
"""))

inf.registerBuiltinInferenceSP("by_extent", \
    deterministic_typed(Extent, [t.ForeignBlobType()], t.ForeignBlobType(), descr="""
Select the choices in the dynamic extent of the current selection.
"""))

inf.registerBuiltinInferenceSP("by_union", \
    deterministic_typed(lambda *args: Union(args), [t.ForeignBlobType()], t.ForeignBlobType(), variadic=True, descr="""
Union the given selections.
"""))

inf.registerBuiltinInferenceSP("by_top", deterministic_typed(Top, [], t.ForeignBlobType(), descr="""
Select the "top" of the model, whose dynamic extent is all random choices.
"""))

inf.registerBuiltinInferenceSP("by_star", deterministic_typed(Star, [], t.ForeignBlobType(), descr="""
Walk to all the random choices in the dynamic extent of the source.
"""))

inf.registerBuiltinInferenceSP("minimal_subproblem", \
    deterministic_typed(MinimalSubproblem, [t.ForeignBlobType()], t.ForeignBlobType(), descr="""
Construct the minimal subproblem from the given selection.
"""))

# XXX Do I want different names for "random singleton variable" vs
# "random singleton block"?  ATM, they can be disambiguated by
# dispatch.
inf.registerBuiltinInferenceSP("random_singleton", \
    deterministic_typed(Random1, [t.ForeignBlobType()], t.ForeignBlobType(), descr="""
Randomly select one component of the current selection.

Correctly account for the acceptance correction due to possible
changes in the probability of selecting a particular subproblem to
work on.

A "component" may be a single random choice, if the current selection
is a set, or a set, if the current selection is a dictionary of tag
values to sets of variables.
"""))

inf.registerBuiltinInferenceSP("esr", \
    deterministic_typed(EsrEdge, [t.IntegerType()], t.ForeignBlobType(),
                        descr="""Walk to the given requested result."""))
