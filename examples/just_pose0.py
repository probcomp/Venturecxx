from collections import Counter
#
import numpy
#
from venture.shortcuts import make_puma_church_prime_ripl


program = """
[assume pose_0
  (scope_include (quote 0) 2
    (list (uniform_continuous -100 100)
          (uniform_continuous -100 100)
          (uniform_continuous -3.14 3.14)
          ))]
"""


def get_ripl():
    ripl = make_puma_church_prime_ripl()
    ripl.execute_program(program)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 0) 0.1))', -.01)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 1) 0.1))', 1.563)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 2) 0.1))', -.000112)
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


N_samples = 100
#infer_string = '(mh 0 2 100)'
infer_string = '(mh default one 100)'
#
ripl = get_ripl()
poses = numpy.array(sample_new_poses(ripl, N_samples))
counter = count_poses(poses)
num_unique_poses = len(set(counter.keys()))
#print '\n'.join(map(str, counter.iteritems()))
#print Counter(counter.values())
print 'infer_string: %s' % infer_string
print 'just_pose0: #unique poses = %s / %s' % (num_unique_poses, N_samples)
