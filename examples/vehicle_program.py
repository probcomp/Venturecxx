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
simulate_gps_str = '(simulate_gps (get_pose %s) %s %s)' % ('%s',
        gps_xy_additive_noise_std, gps_heading_additive_noise_std)
sample_pose_str = '(get_pose %s)'


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

[assume velocity_gamma_rate (scope_include (quote (control))
                                           4
                                           (gamma 1.0 1.0))]

[assume steering_mean (scope_include (quote (control))
                                     5
                                     (normal 0 .1))]

[assume steering_std (scope_include (quote (control))
                                    6
                                    (gamma 1.0 100.0))]

[assume dt (scope_include (quote state) -1
  (mem (lambda (i) (uniform_continuous 0 100))))]

[assume get_ith_timestamp (mem (lambda (i)
  (if (= i 0) 0
              (+ (get_ith_timestamp (- i 1)) (dt i)))))]

[assume get_more_recent_index (lambda (t i)
  (if (> (get_ith_timestamp i) t) i
                                  (get_more_recent_index t (+ i 1))))]

[assume get_last_index_at_t (lambda (t) (- (get_more_recent_index t 0) 1))]

[assume get_control_i (scope_include (quote state) -2
  (mem (lambda (i coord)
    (if (= coord 0)
        (gamma 1.0 velocity_gamma_rate)
        (normal steering_mean steering_std)
        ))))]

[assume get_control_at_t (lambda (t)
  (list (get_control_i (get_last_index_at_t t) 0)
        (get_control_i (get_last_index_at_t t) 1)
        ))]

[assume get_last_control_t_at_t (lambda (t)
  (get_ith_timestamp (get_last_index_at_t t)))]

[assume get_dt_since_last_control (lambda (t)
  (- t (get_ith_timestamp (get_last_index_at_t t))))]

"""

program_assumes = """

[assume initial_pose (scope_include (quote state) 0 (list (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)))]

[assume get_pose (mem (lambda (t)
  (if (= t 0) initial_pose
              (scope_include (quote state) t (simulate_motion
                                             (get_dt_since_last_control t)
                                             (get_pose (get_last_control_t_at_t t))
                                             (get_control_at_t t)
                                             vehicle_params
                                             fractional_xy_error_std
                                             fractional_heading_error_std
                                             additive_xy_error_std
                                             additive_heading_error_std
                                             )))))]

"""

program = program_constants + program_hypers + program_control_generation + program_assumes
