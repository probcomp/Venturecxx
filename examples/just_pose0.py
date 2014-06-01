from itertools import product
from collections import Counter
#
import numpy
#
from venture.shortcuts import make_puma_church_prime_ripl


short_program = """
[assume pose_0
  (scope_include (quote 0) 2
    (list (uniform_continuous -100 100)
          (uniform_continuous -100 100)
          (uniform_continuous -3.14 3.14)
          ))]
"""

long_program = """
[assume vehicle_params (list 0.299541 0.0500507 0 0.257717)]



[assume fractional_xy_error_std (scope_include (quote parameters)
                                               0
                                               (gamma 1.0 100.0))]

[assume fractional_heading_error_std (scope_include (quote parameters)
                                                    1
                                                    (gamma 1.0 100.0))]

[assume additive_xy_error_std (scope_include (quote parameters)
                                             2
                                             (gamma 1.0 100.0))]

[assume additive_heading_error_std (scope_include (quote parameters)
                                                  3
                                                  (gamma 1.0 100.0))]

[assume gps_xy_error_std (scope_include (quote parameters)
                                        4
                                        (gamma 1.0 10.0))]

[assume gps_heading_error_std (scope_include (quote parameters)
                                             5
                                             (gamma 1.0 100.0))]

[assume dt_0
(scope_include (quote 0) 0
  (gamma 1.0 1.0))
]
[assume pose_0
(scope_include (quote 0) 2
  (list (uniform_continuous -100 100)
        (uniform_continuous -100 100)
        (uniform_continuous -3.14 3.14)
        ))
]
[assume control_0
(scope_include (quote 0) 1
  (list (uniform_continuous -100 100)
        (uniform_continuous -3.14 3.14)
        ))
]
"""

program_lookup = dict(short_program=short_program, long_program=long_program)


def get_ripl(which_program):
    ripl = make_puma_church_prime_ripl()
    program = program_lookup[which_program]
    ripl.execute_program(program)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 0) 0.1))', -.01)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 1) 0.1))', 1.563)
    ripl.observe('(scope_include (quote 0) 2 (normal (lookup pose_0 2) 0.1))', -.000112)
    ripl.infer('(incorporate)')
    return ripl

def sample_new_pose(ripl, infer_string):
    out = ripl.infer(infer_string)
    return ripl.predict('pose_0')

def sample_new_poses(ripl, infer_string, N):
    return [sample_new_pose(ripl, infer_string) for _i in range(N)]

def count_poses(poses):
    return Counter(map(tuple, poses))

def run_program_with_infer((which_program, infer_string)):
    ripl = get_ripl(which_program)
    poses = numpy.array(sample_new_poses(ripl, infer_string, N_samples))
    counter = count_poses(poses)
    num_unique_poses = len(set(counter.keys()))
    #print '\n'.join(map(str, counter.iteritems()))
    #print Counter(counter.values())
    print 'which_program: %s' % which_program
    print 'infer_string: %s' % infer_string
    print 'just_pose0: #unique poses = %s / %s' % (num_unique_poses, N_samples)
    print


N_samples = 100
infer_strings = ['(mh default one 100)', '(mh 0 2 100)']
which_programs = ['short_program', 'long_program']
map(run_program_with_infer, product(which_programs, infer_strings))
