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

import numbers

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
from venture.lite.infer.mh import mixMH
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

import venture.lite.value as v

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
    return (search.TraceSearchIndexer(selection_blob.datum), transitions, extra)
  else:
    # Assume old scope-block form
    (scope, block, transitions, extra) = parse_arguments(trace, args)
    return (BlockScaffoldIndexer(scope, block), transitions, extra)

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

def primitive_infer(trace, exp):
  operator = exp[0]
  if operator == "mh":
    (scaffolder, transitions, _) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, MHOperator()))
  elif operator == "func_mh":
    (scaffolder, transitions, _) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, FuncMHOperator()))
  elif operator == "draw_scaffold":
    (scaffolder, _transitions, _) = dispatch_arguments(trace, exp)
    drawScaffold(trace, scaffolder)
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
    (scaffolder, transitions, extra) = dispatch_arguments(trace, exp)
    steps = int(extra[0])
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, MeanfieldOperator(steps, 0.0001)))
  elif operator == "hmc":
    (scaffolder, transitions, (epsilon, L)) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, HamiltonianMonteCarloOperator(epsilon, int(L))))
  elif operator == "gibbs":
    (scaffolder, transitions, _) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, EnumerativeGibbsOperator()))
  elif operator == "emap":
    (scaffolder, transitions, _) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, EnumerativeMAPOperator()))
  elif operator == "gibbs_update":
    (scope, block, transitions, _) = parse_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block, updateValues=True),
            EnumerativeGibbsOperator()))
  elif operator == "slice":
    (scaffolder, transitions, (w, m)) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, StepOutSliceOperator(w, m)))
  elif operator == "slice_doubling":
    (scaffolder, transitions, (w, p)) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, DoublingSliceOperator(w, p)))
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
    (scaffolder, transitions, (rate, steps)) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, GradientAscentOperator(rate, int(steps))))
  elif operator == "nesterov":
    (scaffolder, transitions, (rate, steps)) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder,
            NesterovAcceleratedGradientAscentOperator(rate, int(steps))))
  elif operator == "rejection":
    (scaffolder, transitions, extra) = dispatch_arguments(trace, exp)
    if len(extra) == 1:
      trials = int(extra[0])
    else:
      trials = None
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, RejectionOperator(trials)))
  elif operator == "bogo_possibilize":
    (scaffolder, transitions, _) = dispatch_arguments(trace, exp)
    return transloop(trace, transitions, lambda : \
      mixMH(trace, scaffolder, BogoPossibilizeOperator()))
  elif operator == "print_scaffold_stats":
    (scaffolder, _transitions, _) = dispatch_arguments(trace, exp)
    scaffold = scaffolder.sampleIndex(trace)
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
