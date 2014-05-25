import random
import functools
import time
#
import numpy
import pylab
pylab.ion()
pylab.show()
import pandas
#
import slamutils
from contexts import Timer, MemoryContext
from venture.venturemagics.ip_parallel import MRipl
from venture.shortcuts import make_puma_church_prime_ripl


# settings/constants
#
# vehicle
vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717
# simulation/control
constant_velocity = .1
constant_steering = 0
initial_state = (0, 0, 0)
gps_xy_additive_noise_std = 0.1
gps_heading_additive_noise_std = 0.005
# inference
use_mripl = False
N_mripls = 2
N_particles = 16
backend = 'puma'
N_infer = 5
N_steps = 4000
simulate_gps_str = '(simulate_gps (get_pose %s) %s %s)' % ('%s',
        gps_xy_additive_noise_std, gps_heading_additive_noise_std)
base_filename = 'vehicle_just_gps'
gen_filename = lambda idx: base_filename + '_' + ('%04d' % idx) + '.png'


# helpers
def gen_gps(t):
    true_pose = deadreckon.ix[t].reindex(['x', 'y', 'heading']).values
    noise = (
            random.gauss(0, gps_xy_additive_noise_std),
            random.gauss(0, gps_xy_additive_noise_std),
            random.gauss(0, gps_heading_additive_noise_std),
            )
    return (true_pose + noise).tolist()
def observe_N_gps(ripl, N):
    def observe_gps(t):
        def _convert(val):
            def _convert_real(val):
                return {"type":"real","value":val}
            def _convert_list(val):
                return {"type":"vector","value":map(_convert, val)}
            is_list = isinstance(val, (list, tuple))
            return _convert_list(val) if is_list else _convert_real(val)
        _simulate_gps_str = simulate_gps_str % t
        converted = _convert(gen_gps(t))
        return ripl.observe(_simulate_gps_str, converted)
    return map(observe_gps, range(1, N))
def observe_N_control(ripl, N):
    def observe_control(i):
        ripl.observe('(get_control_i %s 0)' % i, constant_velocity)
        ripl.observe('(get_control_i %s 1)' % i, constant_steering)
        ripl.observe('(dt %s)' % i, .25)
        pass
    return map(observe_control, range(1, N))
def gen_infer_str(N_particles, N_infer):
    hypers = '(mh hypers one 3)'
    state = '(pgibbs state ordered %s 1)' % N_particles
    infer_str =  '(cycle (%s %s) %s)' % (hypers, state, N_infer)
    return infer_str
#
def gen_ripl(use_mripl):
    ripl = None
    if use_mripl:
        ripl = MRipl(N_mripls, set_no_engines=N_mripls, backend=backend)
        pass
    else:
        ripl = make_puma_church_prime_ripl()
        pass
    ripl.execute_program(program)
    return ripl
def predict_from_ripl(ripl, N_steps):
    predict_pose = lambda x: ripl.predict('(get_pose %s)' % x)
    return numpy.array(map(predict_pose, range(N_steps)))
def sample_from_prior(N_steps, use_mripl=True):
    ripl = gen_ripl(use_mripl)
    return predict_from_ripl(ripl, N_steps)
#
def _plot(samples, color='r'):
    def _plot_run(run):
        return pylab.plot(run[:, 0], run[:, 1], '-x', color=color, alpha=0.2)
    def get_run_i(i):
        return samples[:, i, :]
    is_mripl = len(samples.shape) == 3
    if is_mripl:
        map(_plot_run, map(get_run_i, range(samples.shape[1])))
        pass
    else:
        _plot_run(samples)
        pass
    return
def plot(from_prior, from_posterior, filename=None):
    filename = filename if filename is not None else base_filename + '.png'
    pylab.figure()
    _plot(from_prior, color='r')
    _plot(from_posterior, color='g')
    pylab.savefig(filename)
    pylab.close()
    return
#
def measure_time_and_memory(task, func, *args, **kwargs):
    with MemoryContext(task) as mc:
        with Timer(task) as t:
            out = func(*args, **kwargs)
            pass
        pass
    return mc, t, out


# generate deadreckoning (ground truth for these purposes)
gen_control = lambda t: (constant_velocity, constant_steering)
controls = map(gen_control, range(N_steps))
control_columns = ['Velocity', 'Steering']
control_frame = pandas.DataFrame(controls, columns=control_columns)
deadreckon = slamutils.DeadReckoning(initial_state, control_frame)


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

""" % (
        vehicle_a, vehicle_b, vehicle_h, vehicle_L,
        #constant_velocity, constant_steering,
        )

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

[assume velocity_gamma_rate (scope_include (quote (hypers))
                                           4
                                           (gamma 1.0 1.0))]

[assume steering_mean (scope_include (quote (hypers))
                                     5
                                     (gamma 1.0 100.0))]

[assume steering_std (scope_include (quote (hypers))
                                    6
                                    (gamma 1.0 100.0))]

"""

program_control_generation = """

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

"""

program_assumes = """

[assume initial_pose (scope_include (quote state) 0 (list (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)
                                                          (uniform_continuous -1 1)))]

[assume get_pose (mem (lambda (t)
  (if (= t 0) initial_pose
              (scope_include (quote state) t (simulate_motion 1
                                             (get_pose (- t 1))
                                             (get_control_at_t t)
                                             vehicle_params
                                             fractional_xy_error_std
                                             fractional_heading_error_std
                                             additive_xy_error_std
                                             additive_heading_error_std
                                             )))))]

"""

program = program_constants + program_hypers + program_control_generation + program_assumes


# ripl with NO observes
task = 'sample_from_prior'
mc, t, from_prior = measure_time_and_memory(task, sample_from_prior, N_steps, use_mripl)


# ripl with observes
task = 'posterior ripl setup'
mc, t, posterior_ripl = measure_time_and_memory(task, gen_ripl, use_mripl)
#
task = 'posterior ripl gps observes'
mc, t, out = measure_time_and_memory(task, observe_N_gps, posterior_ripl, N_steps)
#
task = 'posterior ripl control observes'
mc, t, out = measure_time_and_memory(task, observe_N_control, posterior_ripl, N_steps)
#
task = 'posterior predict_from_ripl before infer'
mc, t, from_posterior = measure_time_and_memory(task, predict_from_ripl, posterior_ripl, N_steps)
#
filename = gen_filename(0)
task = 'plot posterior predict_from_ripl before infer'
mc, t, out = measure_time_and_memory(task, plot, from_prior, from_posterior, filename)
#
step_by = 1
infer_str = gen_infer_str(N_particles, step_by)
for idx in range(1, N_infer / step_by + 1):
    task = infer_str
    mc, t, out = measure_time_and_memory(task, posterior_ripl.infer, infer_str)
    #
    task = 'posterior predict_from_ripl'
    mc, t, from_posterior = measure_time_and_memory(task, predict_from_ripl, posterior_ripl, N_steps)
    #
    filename = gen_filename(idx)
    task = 'plotting %s' % filename
    mc, t, out = measure_time_and_memory(task, plot, from_prior, from_posterior, filename)
    pass
