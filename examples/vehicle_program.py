# settings/constants
#
# vehicle
vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717
# simulation/control
gps_xy_additive_noise_std = 0.1
gps_heading_additive_noise_std = 0.005
# inference
use_mripl = False
N_mripls = 2
N_particles = 16
backend = 'puma'
N_infer = 5
N_steps = 4000
#
simulate_gps_substitution = ('%s', gps_xy_additive_noise_std, gps_heading_additive_noise_std)
simulate_gps_str = '(simulate_gps (get_pose_i %s) %s %s)' % simulate_gps_substitution
sample_pose_str = '(get_pose_i %s)'
sample_dt_str = '(get_dt_i %s)'
get_control_str = '(_get_control_i %s %s)'
infer_hypers_str = '(mh hypers one %s)' % N_infer
infer_state_str = '(mh state one %s)' % N_infer
infer_args = [infer_hypers_str, infer_state_str]


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

""" % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)

program_hypers = """

[assume fractional_xy_error_std (scope_include (quote hypers)
                                               0
                                               (gamma 1.0 100.0))]

[assume fractional_heading_error_std (scope_include (quote hypers)
                                                    1
                                                    (gamma 1.0 100.0))]

[assume additive_xy_error_std (scope_include (quote hypers)
                                             2
                                             (gamma 1.0 100.0))]

[assume additive_heading_error_std (scope_include (quote hypers)
                                                  3
                                                  (gamma 1.0 100.0))]

"""

program_control_generation = """

[assume velocity_gamma_rate (gamma 1.0 1.0)]

[assume steering_mean (normal 0 .1)]

[assume steering_std (gamma 1.0 100.0)]

[assume get_dt_i (mem (lambda (i) (uniform_continuous 0 100)))]

[assume _get_control_i
  (mem (lambda (i coord)
    (if (= coord 0)
        (normal .1 velocity_gamma_rate)
        (normal steering_mean steering_std)
        )))]

[assume get_control_i (lambda (i)
  (list (_get_control_i i 0)
        (_get_control_i i 1)
        ))]

"""

program_assumes = """

[assume initial_pose (scope_include (quote state) 0 (list (uniform_continuous -100 100)
                                                          (uniform_continuous -100 100)
                                                          (uniform_continuous -3.14 3.14)
                                                          ))]

[assume get_pose_i (mem (lambda (i)
  (if (= i 0) initial_pose
              (scope_include (quote state) i (simulate_motion (get_dt_i (- i 1))
                                                              (get_pose_i (- i 1))
                                                              (get_control_i (- i 1))
                                                              vehicle_params
                                                              fractional_xy_error_std
                                                              fractional_heading_error_std
                                                              additive_xy_error_std
                                                              additive_heading_error_std
                                                              )))))]

"""

program = program_constants + program_hypers + program_control_generation + program_assumes
