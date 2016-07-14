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

def parse_arguments(trace, args):
  assert len(args) >= 3
  (_, scope, block) = args[0:3]
  scope, block = trace._normalizeEvaluatedScopeAndBlock(scope, block)
  if len(args) == 3:
    transitions = 1
  else:
    maybe_transitions = args[-1]
    if isinstance(maybe_transitions, bool):
      # The last item was the parallelism indicator, which Lite
      # ignores anyway
      transitions = int(args[-2])
    else:
      transitions = int(args[-1])
  if not trace.scopeHasEntropy(scope):
    transitions = 0
  return (scope, block, transitions)

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
  (scope, block, transitions) = parse_arguments(trace, exp)
  if operator == "mh":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block), MHOperator()))
  elif operator == "func_mh":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block), FuncMHOperator()))
  elif operator == "draw_scaffold":
    return transloop(trace, transitions, lambda : \
      drawScaffold(trace, BlockScaffoldIndexer(scope, block)))
  elif operator == "mh_kernel_update":
    return transloop(trace, transitions, lambda : \
      do_mh_kernel_update(trace, scope, block, exp))
  elif operator == "subsampled_mh":
    return transloop(trace, transitions, lambda : \
      do_subsampled_mh(trace, scope, block, exp))
  elif operator == "subsampled_mh_check_applicability":
    SubsampledBlockScaffoldIndexer(scope, block).checkApplicability(trace)
    # Does not affect nodes
    return 0.0
  elif operator == "subsampled_mh_make_consistent":
    return transloop(trace, transitions, lambda : \
      do_subsampled_mh_make_consistent(trace, scope, block, exp))
  elif operator == "meanfield":
    steps = int(exp[3])
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            MeanfieldOperator(steps, 0.0001)))
  elif operator == "hmc":
    (epsilon, L) = exp[3:5]
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            HamiltonianMonteCarloOperator(epsilon, int(L))))
  elif operator == "gibbs":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            EnumerativeGibbsOperator()))
  elif operator == "emap":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            EnumerativeMAPOperator()))
  elif operator == "gibbs_update":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block, updateValues=True),
            EnumerativeGibbsOperator()))
  elif operator == "slice":
    (w, m) = exp[3:5]
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            StepOutSliceOperator(w, m)))
  elif operator == "slice_doubling":
    (w, p) = exp[3:5]
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            DoublingSliceOperator(w, p)))
  elif operator == "pgibbs":
    particles = int(exp[3])
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
    particles = int(exp[3])
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
    particles = int(exp[3])
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
    particles = int(exp[3])
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
    (rate, steps) = exp[3:5]
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            GradientAscentOperator(rate, int(steps))))
  elif operator == "nesterov":
    (rate, steps) = exp[3:5]
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            NesterovAcceleratedGradientAscentOperator(rate, int(steps))))
  elif operator == "rejection":
    if len(exp) == 5:
      trials = int(exp[3])
    else:
      trials = None
      return transloop(trace, transitions, lambda : \
        mixMH(trace, BlockScaffoldIndexer(scope, block),
              RejectionOperator(trials)))
  elif operator == "bogo_possibilize":
    return transloop(trace, transitions, lambda : \
      mixMH(trace, BlockScaffoldIndexer(scope, block),
            BogoPossibilizeOperator()))
  elif operator == "print_scaffold_stats":
    scaffold = BlockScaffoldIndexer(scope, block).sampleIndex(trace)
    scaffold.show()
    return scaffold.numAffectedNodes()
  else: raise Exception("INFER %s is not implemented" % operator)

def do_mh_kernel_update(trace, scope, block, exp):
  (useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:6]
  scaffolder = BlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return mixMH(trace, scaffolder, MHOperator())

def do_subsampled_mh(trace, scope, block, exp):
  (Nbatch, k0, epsilon,
   useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:9]
  scaffolder = SubsampledBlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return subsampledMixMH(
    trace, scaffolder, SubsampledMHOperator(), Nbatch, k0, epsilon)

def do_subsampled_mh_make_consistent(trace, scope, block, exp):
  (useDeltaKernels, deltaKernelArgs, updateValues) = exp[3:6]
  scaffolder = SubsampledBlockScaffoldIndexer(scope, block,
    useDeltaKernels=useDeltaKernels, deltaKernelArgs=deltaKernelArgs,
    updateValues=updateValues)
  return SubsampledMHOperator().makeConsistent(trace, scaffolder)
