from collections import Counter
#
import numpy
#
from venture.shortcuts import make_puma_church_prime_ripl


program = """
[assume pose_0
  (scope_include (quote 0) 0
    (list (uniform_continuous -100 100)
          (uniform_continuous -100 100)
          (uniform_continuous -3.14 3.14)
          ))]
"""


# infer_string = '(mh 0 0 100)'
infer_string = '(mh default one 100)'


def get_ripl():
    ripl = make_puma_church_prime_ripl()
    ripl.execute_program(program)
    ripl.observe('(normal (lookup pose_0 0) 0.1)', -.01)
    ripl.observe('(normal (lookup pose_0 1) 0.1)', 1.563)
    ripl.observe('(normal (lookup pose_0 2) 0.1)', -.000112)
    ripl.infer('(incorporate)')
    out = ripl.infer(infer_string)
    return ripl

def sample_new_pose(ripl):
    out = ripl.infer(infer_string)
    return ripl.predict('pose_0')

def sample_new_poses(ripl, N):
    return [sample_new_pose(ripl) for _i in range(N)]

def count_poses(poses):
    return Counter(map(tuple, poses))

ripl = get_ripl()
poses = numpy.array(sample_new_poses(ripl, 100))
counter = count_poses(poses)
print '\n'.join(map(str, counter.iteritems()))
print Counter(counter.values())
