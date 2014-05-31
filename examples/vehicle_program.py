# settings/constants
#
# vehicle
vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717
# inference
use_mripl = False
N_mripls = 2
N_particles = 16
backend = 'puma'
N_infer = 50


# assume/observe helpers
dt_name_str = 'dt_%d'
random_dt_value_str = """
(scope_include (quote %d) 0
  (gamma 1.0 1.0))
"""
control_name_str = 'control_%d'
control_value_str = '(list %s %s)'
random_control_value_str = """
(scope_include (quote %d) 1
  (list (uniform_continuous -100 100)
        (uniform_continuous -3.14 3.14)
        ))
"""
pose_name_str = 'pose_%d'
get_pose_value_str = lambda i: """
(scope_include (quote %d) 2
  (simulate_motion dt_%d
                   pose_%d
                   control_%d
                   vehicle_params
                   fractional_xy_error_std
                   fractional_heading_error_std
                   additive_xy_error_std
                   additive_heading_error_std
                   ))
""" % (i, i-1, i-1, i-1)
random_pose_value_str = """
(scope_include (quote %d) 2
  (list (uniform_continuous -100 100)
        (uniform_continuous -100 100)
        (uniform_continuous -3.14 3.14)
        ))
"""
get_observe_gps_str = lambda i: """
(scope_include (quote %d) 3
  (simulate_gps pose_%d gps_xy_error_std gps_heading_error_std))
""" % (i, i)
# ORDER: do_assume_dt, do_assume_control, do_assume_pose, do_observe_gps
def get_assume_as_program(string, value, scope_block_str=None):
    if scope_block_str is not None:
        return '[assume (scope_include %s %s %s)]' % (scope_block_str, string, value)
    else:
        return '[assume %s %s]' % (string, value)
def do_assume(ripl, string, value):
    return ripl.assume(string, value, label=string)
def do_assume_dt(ripl, i, dt):
    string = dt_name_str % i
    value = dt
    return do_assume(ripl, string, value)
def do_assume_control(ripl, i, velocity, steering):
    string = control_name_str % i
    value = control_value_str % (velocity, steering)
    return do_assume(ripl, string, value)
def do_assume_random_control(ripl, i):
    string = control_name_str % i
    value = random_control_value_str % i
    return do_assume(ripl, string, value)
def do_assume_pose(ripl, i):
    string = pose_name_str % i
    value = get_pose_value_str(i)
    return do_assume(ripl, string, value)
def do_observe(ripl, string, value, label=None):
    label = string if label is None else label
    return ripl.observe(string, value, label=label)
def do_observe_gps(ripl, i, gps_value):
    def _wrap(val):
        def _wrap_real(val):
            return dict(type='real', value=val)
        def _wrap_list(val):
            return dict(type='vector', value=map(_wrap, val))
        is_list = isinstance(val, (list, tuple))
        return _wrap_list(val) if is_list else _wrap_real(val)
    string = get_observe_gps_str(i)
    value = _wrap(gps_value)
    label = 'gps_%d' % i
    return do_observe(ripl, string, value, label=label)
# infer helpers
infer_parameters_str = '(mh parameters one %d)' % N_infer
infer_state_str = '(mh %s all %d)' % ('%d', N_infer)
get_infer_args = lambda i: [infer_parameters_str, infer_state_str % i]


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

""" % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)

program_parameters = """

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

"""

program_assumes = '\n'.join([
    get_assume_as_program(dt_name_str % 0, random_dt_value_str % 0),
    get_assume_as_program(pose_name_str % 0, random_pose_value_str % 0),
    get_assume_as_program(control_name_str % 0, random_control_value_str % 0),
    ])

program = program_constants + program_parameters + program_assumes
