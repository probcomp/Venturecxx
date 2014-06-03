# settings/constants
#
# vehicle
vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717
# inference
use_mripl = True
N_mripls = 64
N_particles = 16
backend = 'puma'
N_infer = 100


# assume/observe helpers
get_dt_name_str = lambda i: 'dt_%d' % i
get_random_dt_value_str = lambda i: """
(scope_include %d 0 (gamma 1.0 100.0))
""" % i
get_control_name_str = lambda i: 'control_%d' % i
get_control_value_str = lambda i, j: '(list %s %s)' % (i, j)
get_random_control_value_str = lambda i: """
(list
  (scope_include %d 0 (uniform_continuous -.01 .2))
  (scope_include %d 1 (uniform_continuous -.314 .314))
  )
""" % (i, i)
get_pose_name_str = lambda i: 'pose_%d' % i
get_pose_value_str = lambda i: """
(scope_include %d 2
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
get_random_pose_value_str = lambda i: """
(list
  (scope_include %d 3 (uniform_continuous -10 10))
  (scope_include %d 4 (uniform_continuous -10 10))
  (scope_include %d 5 (uniform_continuous -3.14 3.14))
  )
""" % (i, i, i)
get_observe_gps_str = lambda i: """
(scope_include %d 6
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
    string = get_dt_name_str(i)
    value = dt
    return do_assume(ripl, string, value)
def do_assume_control(ripl, i, velocity, steering):
    string = get_control_name_str(i)
    value = get_control_value_str(velocity, steering)
    return do_assume(ripl, string, value)
def do_assume_random_control(ripl, i):
    string = get_control_name_str(i)
    value = get_random_control_value_str(i)
    return do_assume(ripl, string, value)
def do_assume_pose(ripl, i):
    string = get_pose_name_str(i)
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
infer_parameters_str = '(mh parameters one %d)'
infer_state_str = '(cycle ((mh %d one 1) (mh default one 1)) %d)'
def get_infer_args(i, N=N_infer, hypers=True):
    if hypers:
        return [infer_parameters_str % N, infer_state_str % (i, N)]
    else:
        return [infer_state_str % (i, N)]


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
    get_assume_as_program(get_dt_name_str(0), get_random_dt_value_str(0)),
    get_assume_as_program(get_pose_name_str(0), get_random_pose_value_str(0)),
    get_assume_as_program(get_control_name_str(0), get_random_control_value_str(0)),
    ])

program = program_constants + program_parameters + program_assumes
