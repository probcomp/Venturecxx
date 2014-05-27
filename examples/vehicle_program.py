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
N_infer = 5


# assume/observe helpers
dt_name_str = 'dt_%s'
control_name_str = 'control_%s'
control_value_str = '(list %s %s)'
pose_name_str = 'pose_%s'
get_pose_value_str = lambda i: """
(scope_include (quote %s) 0
  (simulate_motion dt_%s
                   pose_%s
                   control_%s
                   vehicle_params
                   fractional_xy_error_std
                   fractional_heading_error_std
                   additive_xy_error_std
                   additive_heading_error_std
                   ))
""" % (i, i-1, i-1, i-1)
get_observe_gps_str = lambda i: """
(scope_include (quote %s) 0
  (simulate_gps pose_%s gps_xy_noise_std gps_heading_noise_std)
""" % (i, i)
# ORDER: do_assume_dt, do_assume_control, do_assume_pose, do_observe_gps
def get_assume(string, value):
    return '[assume %s %s]' % (string, value)
def do_assume(ripl, string, value):
    program = get_assume(string, value)
    return ripl.execute_program(program)
def do_assume_dt(ripl, i, dt):
    string = dt_name_str % i
    value = dt
    return do_assume(ripl, string, value)
def do_assume_control(ripl, i, velocity, steering):
    string = control_name_str % i
    value = control_value_str % (velocity, steering)
    return do_assume(ripl, string, value)
def do_assume_pose(ripl, i):
    string = pose_name_str % i
    value = get_pose_value_str(i)
    return do_assume(ripl, string, value)
def do_observe(ripl, string, value):
    return ripl.observe(string, value)
def do_observe_gps(ripl, i, gps_value):
    string = get_observe_gps_str(i)
    value = _wrap(gps_value)
    return do_observe(ripl, string, value)
# infer helpers
infer_parameters_str = '(mh parameters one %s)' % N_infer
infer_state_str = '(mh %s one %s)' % N_infer
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

[assume gps_xy_noise_std (scope_include (quote parameters)
                                        4
                                        (gamma 1.0 10.0))]

[assume gps_heading_noise_std (scope_include (quote parameters)
                                             5
                                             (gamma 1.0 100.0))]

"""

program_assumes = """

[assume pose_0 (scope_include (quote 0) 0
  (list (uniform_continuous -100 100)
        (uniform_continuous -100 100)
        (uniform_continuous -3.14 3.14)
        ))]

"""

program = program_constants + program_parameters + program_assumes
