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

from collections import OrderedDict
import numbers

from venture.lite.detach import detachAndExtract
from venture.lite.infer.draw_scaffold import drawScaffold
from venture.lite.infer.egibbs import EnumerativeGibbsOperator
from venture.lite.infer.egibbs import EnumerativeMAPOperator
from venture.lite.infer.hmc import HamiltonianMonteCarloOperator
from venture.lite.infer.map_gradient import GradientAscentOperator
from venture.lite.infer.map_gradient import NesterovAcceleratedGradientAscentOperator
from venture.lite.infer.meanfield import MeanfieldOperator
from venture.lite.infer.mh import BlockScaffoldIndexer
from venture.lite.infer.mh import FuncMHOperator
from venture.lite.infer.mh import MHOperator
from venture.lite.infer.mh import getCurrentValues
from venture.lite.infer.mh import mixMH
from venture.lite.infer.mh import registerDeterministicLKernels
from venture.lite.infer.pgibbs import PGibbsOperator
from venture.lite.infer.pgibbs import ParticlePGibbsOperator
from venture.lite.infer.pgibbs import ParticlePMAPOperator
from venture.lite.infer.rejection import BogoPossibilizeOperator
from venture.lite.infer.rejection import RejectionOperator
from venture.lite.infer.slice_sample import DoublingSliceOperator
from venture.lite.infer.slice_sample import StepOutSliceOperator
from venture.lite.infer.subsampled_mh import SubsampledBlockScaffoldIndexer
from venture.lite.infer.subsampled_mh import SubsampledMHOperator
from venture.lite.infer.subsampled_mh import subsampledMixMH
from venture.lite.regen import regenAndAttach
import venture.lite.value as v
import venture.lite.types as t

def parse_arguments(trace, args):
  assert len(args) >= 3
  (_, scope, block) = args[0:3]
  scope, block = trace._normalizeEvaluatedScopeAndBlock(scope, block)
  (transitions, extra) = parse_transitions_extra(args[3:])
  if not trace.scopeHasEntropy(scope):
    transitions = 0
  return (scope, block, transitions, extra)

def parse_transitions_extra(args):
  if len(args) == 0:
    transitions = 1
    extra = []
  else:
    maybe_transitions = args[-1]
    if isinstance(maybe_transitions, bool):
      # The last item was the parallelism indicator, which Lite
      # ignores anyway
      transitions = int(args[-2])
      extra = args[:-2]
    elif isinstance(maybe_transitions, numbers.Number):
      transitions = int(args[-1])
      extra = args[:-1]
    elif isinstance(maybe_transitions, v.VentureNumber):
      # Transitions came in without type unwrapping
      transitions = int(args[-1].getNumber())
      extra = args[:-1]
    elif isinstance(maybe_transitions, v.VentureBool):
      # Arguments came in without type unwrapping
      transitions = int(args[-2].getNumber())
      extra = args[:-2]
  return (transitions, extra)

def dispatch_arguments(trace, args):
  import venture.untraced.trace_search as search
  if isinstance(args[1], v.VentureForeignBlob) and search.is_search_ast(args[1].datum):
    # Assume new subproblem selector form
    (_, selection_blob) = args[0:2]
    (transitions, extra) = parse_transitions_extra(args[2:])
    # TODO Detect the case when the selection is guaranteed to produce
    # no random choices and abort (like parse_arguments does)
    return ([search.TraceSearchIndexer(selection_blob.datum)], transitions, extra)
  else:
    # Assume old scope-block form
    (scope, block, transitions, extra) = parse_arguments(trace, args)
    if block == "each":
      the_scope = trace.getScope(scope)
      blocks = the_scope.keys()
      return ([BlockScaffoldIndexer(scope, b) for b in blocks], transitions, extra)
    else:
      return ([BlockScaffoldIndexer(scope, block)], transitions, extra)

def transloop(trace, transitions, operate):
  ct = 0
  for _ in range(transitions):
    ct += operate()
    for node in trace.aes:
      trace.madeSPAt(node).AEInfer(trace.madeSPAuxAt(node), trace.np_rng)
    ct += len(trace.aes)

  if transitions > 0:
    return ct/float(transitions)
  else:
    return 0.0

def scaffolder_loop(scaffolders, operate):
  def doit():
    ct = 0
    for scaffolder in scaffolders:
      ct += operate(scaffolder)
    return ct/len(scaffolders)
  return doit

def primitive_infer(trace, exp):
  operator = exp[0]
  if operator == "mh":
    (scaffolders, transitions, _) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, MHOperator())
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "func_mh":
    (scaffolders, transitions, _) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, FuncMHOperator())
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "draw_scaffold":
    (scaffolders, _transitions, _) = dispatch_arguments(trace, exp)
    drawScaffold(trace, scaffolders[0])
  elif operator == "mh_kernel_update":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      do_mh_kernel_update(trace, scope, block, extra))
  elif operator == "subsampled_mh":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      do_subsampled_mh(trace, scope, block, extra))
  elif operator == "subsampled_mh_check_applicability":
    (scope, block, _transitions, _) = parse_arguments(trace, exp)
    SubsampledBlockScaffoldIndexer(scope, block).checkApplicability(trace)
    # Does not affect nodes
    return 0.0
  elif operator == "subsampled_mh_make_consistent":
    (scope, block, transitions, _) = parse_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      do_subsampled_mh_make_consistent(trace, scope, block, extra))
  elif operator == "meanfield":
    (scaffolders, transitions, extra) = dispatch_arguments(trace, exp)
    steps = int(extra[0])
    def doit(scaffolder):
      return mixMH(trace, scaffolder, MeanfieldOperator(steps, 0.0001))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "hmc":
    (scaffolders, transitions, (epsilon, L)) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, HamiltonianMonteCarloOperator(epsilon, int(L)))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "gibbs":
    (scaffolders, transitions, _) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, EnumerativeGibbsOperator())
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "emap":
    (scaffolders, transitions, _) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, EnumerativeMAPOperator())
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "gibbs_update":
    (scope, block, transitions, _) = parse_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block, updateValues=True),
            EnumerativeGibbsOperator()))
  elif operator == "slice":
    (scaffolders, transitions, (w, m)) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, StepOutSliceOperator(w, m))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "slice_doubling":
    (scaffolders, transitions, (w, p)) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, DoublingSliceOperator(w, p))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "pgibbs":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    particles = int(extra[0])
    if isinstance(block, list): # Ordered range
      (_, min_block, max_block) = block
      scaffolder = BlockScaffoldIndexer(scope, "ordered_range",
                                        (min_block, max_block))
      return transloop(trace, transitions, lambda : \
        mixMH(trace, scaffolder, PGibbsOperator(particles)))
    else:
      return transloop(trace, transitions, lambda : \
        mixMH(trace, BlockScaffoldIndexer(scope, block),
              PGibbsOperator(particles)))
  elif operator == "pgibbs_update":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    particles = int(extra[0])
    if isinstance(block, list): # Ordered range
      (_, min_block, max_block) = block
      scaffolder = BlockScaffoldIndexer(
        scope, "ordered_range",
        (min_block, max_block), updateValues=True)
      return transloop(trace, transitions, lambda : \
        mixMH(trace, scaffolder, PGibbsOperator(particles)))
    else:
      return transloop(trace, transitions, lambda : \
        mixMH(trace, BlockScaffoldIndexer(scope, block, updateValues=True),
              PGibbsOperator(particles)))
  elif operator == "func_pgibbs":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    particles = int(extra[0])
    if isinstance(block, list): # Ordered range
      (_, min_block, max_block) = block
      scaffolder = BlockScaffoldIndexer(scope, "ordered_range",
                                        (min_block, max_block))
      return transloop(trace, transitions, lambda : \
        mixMH(trace, scaffolder, ParticlePGibbsOperator(particles)))
    else:
      return transloop(trace, transitions, lambda : \
        mixMH(trace, BlockScaffoldIndexer(scope, block),
              ParticlePGibbsOperator(particles)))
  elif operator == "func_pmap":
    (scope, block, transitions, extra) = parse_arguments(trace, exp)
    particles = int(extra[0])
    if isinstance(block, list): # Ordered range
      (_, min_block, max_block) = block
      scaffolder = BlockScaffoldIndexer(scope, "ordered_range",
                                        (min_block, max_block))
      return transloop(trace, transitions, lambda : \
        mixMH(trace, scaffolder, ParticlePMAPOperator(particles)))
    else:
      return transloop(trace, transitions, lambda : \
        mixMH(trace, BlockScaffoldIndexer(scope, block),
              ParticlePMAPOperator(particles)))
  elif operator == "grad_ascent":
    (scaffolders, transitions, (rate, steps)) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, GradientAscentOperator(rate, int(steps)))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "nesterov":
    (scaffolders, transitions, (rate, steps)) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder,
                   NesterovAcceleratedGradientAscentOperator(rate, int(steps)))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "rejection":
    (scaffolders, transitions, extra) = dispatch_arguments(trace, exp)
    if len(extra) >= 1 and extra[0] in t.NumberType():
      logBound = extra[0].getNumber()
    else:
      logBound = None
    if len(extra) == 2:
      trials = int(extra[1])
    else:
      trials = None
    def doit(scaffolder):
      return mixMH(trace, scaffolder, RejectionOperator(logBound, trials))
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "bogo_possibilize":
    (scaffolders, transitions, _) = dispatch_arguments(trace, exp)
    def doit(scaffolder):
      return mixMH(trace, scaffolder, BogoPossibilizeOperator())
    return transloop(trace, transitions, scaffolder_loop(scaffolders, doit))
  elif operator == "print_scaffold_stats":
    (scaffolders, _transitions, _) = dispatch_arguments(trace, exp)
    scaffold = scaffolders[0].sampleIndex(trace)
    scaffold.show()
    return scaffold.numAffectedNodes()
  else: raise Exception("INFER %s is not implemented" % operator)

def do_mh_kernel_update(trace, scope, block, extra):
  (useDeltaKernels, deltaKernelArgs, updateValues) = extra
  scaffolder = BlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return mixMH(trace, scaffolder, MHOperator())

def do_subsampled_mh(trace, scope, block, extra):
  (Nbatch, k0, epsilon,
   useDeltaKernels, deltaKernelArgs, updateValues) = extra
  scaffolder = SubsampledBlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return subsampledMixMH(
    trace, scaffolder, SubsampledMHOperator(), Nbatch, k0, epsilon)

def do_subsampled_mh_make_consistent(trace, scope, block, extra):
  (useDeltaKernels, deltaKernelArgs, updateValues) = extra
  scaffolder = SubsampledBlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return SubsampledMHOperator().makeConsistent(trace, scaffolder)

def log_likelihood_at(trace, args):
  (scaffolders, transitions, _) = dispatch_arguments(trace, ("bogon",) + args)
  if transitions > 0:
    # Don't want to think about the interaction between 'each' and the
    # value this is supposed to return.
    assert len(scaffolders) == 1, "log_likelihood_at doesn't support 'each'"
    scaffold = scaffolders[0].sampleIndex(trace)
    (_rhoWeight, rhoDB) = detachAndExtract(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, True, rhoDB, OrderedDict())
    # Old state restored, don't need to do anything else
    return xiWeight
  else:
    return 0.0

def log_joint_at(trace, args):
  (scaffolders, transitions, _) = dispatch_arguments(trace, ("bogon",) + args)
  if transitions > 0:
    # Don't want to think about the interaction between 'each' and the
    # value this is supposed to return.
    assert len(scaffolders) == 1, "log_joint_at doesn't support 'each'"
    scaffold = scaffolders[0].sampleIndex(trace)
    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace, pnodes)
    registerDeterministicLKernels(trace, scaffold, pnodes, currentValues,
      unconditional=True)
    (_rhoWeight, rhoDB) = detachAndExtract(trace, scaffold)
    xiWeight = regenAndAttach(trace, scaffold, True, rhoDB, OrderedDict())
    # Old state restored, don't need to do anything else
    return xiWeight
  else:
    return 0.0
