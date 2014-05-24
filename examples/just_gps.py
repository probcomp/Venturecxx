import random
import functools
#
import numpy
import pylab
pylab.ion()
pylab.show()
import pandas
#
import slamutils
from venture.venturemagics.ip_parallel import MRipl


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
N_mripls = 64
N_particles = 32
backend = 'puma'
N_infer = 100
N_steps = 10
simulate_gps_str = '(simulate_gps (get_pose %s) %s %s)' % ('%s',
        gps_xy_additive_noise_std, gps_heading_additive_noise_std)
base_filename = 'vehicle_justs_gps'

# helpers
def gen_gps(t):
    true_pose = deadreckon.ix[t].reindex(['x', 'y', 'heading']).values
    noise = (
            random.gauss(0, gps_xy_additive_noise_std),
            random.gauss(0, gps_xy_additive_noise_std),
            random.gauss(0, gps_heading_additive_noise_std),
            )
    return (true_pose + noise).tolist()
def _convert_real(val):
    return {"type":"real","value":val}
def _convert_list(val):
    return {"type":"vector","value":map(_convert, val)}
def _convert(val):
    is_list = isinstance(val, (list, tuple))
    val = _convert_list(val) if is_list else _convert_real(val)
    return val
_observe_gps = lambda ripl, t: \
        ripl.observe(simulate_gps_str % t, _convert(gen_gps(t)))
_predict_pose = lambda ripl, x: ripl.predict('(get_pose %s)' % x)
gen_infer_str = lambda N_particles, N_infer: \
        '(pgibbs default ordered %s %s)' % (N_particles, N_infer)
#
def gen_ripl():
    ripl = MRipl(N_mripls, backend=backend)
    ripl.execute_program(program)
    return ripl
def predict_from_ripl(ripl, N_steps):
    predict_pose = functools.partial(_predict_pose, ripl)
    return numpy.array(map(predict_pose, range(N_steps)))
def sample_from_prior(N_steps, N_infer):
    ripl = gen_ripl()
    infer_str = gen_infer_str(N_steps, N_infer)
    ripl.infer(infer_str)
    return predict_from_ripl(ripl, N_steps)
#
def _plot(samples, color='r'):
    for run_idx in range(samples.shape[1]):
        pylab.plot(samples[:, run_idx, 0], samples[:, run_idx, 1],
                '-x', color=color, alpha=0.2)
        pass
    return
def plot(from_prior, from_posterior, filename=None):
    filename = filename if filename is not None else base_filename + '.png'
    pylab.figure()
    _plot(from_prior, color='r')
    _plot(from_posterior, color='g')
    pylab.savefig(filename)
    return


# generate deadreckoning (ground truth for these purposes)
gen_control = lambda t: (constant_velocity, constant_steering)
controls = map(gen_control, range(N_steps))
control_columns = ['Velocity', 'Steering']
control_frame = pandas.DataFrame(controls, columns=control_columns)
deadreckon = slamutils.DeadReckoning(initial_state, control_frame)


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

[assume constant_control (list %s %s)]

""" % (
        vehicle_a, vehicle_b, vehicle_h, vehicle_L,
        constant_velocity, constant_steering,
        )

program_assumes = """

[assume fractional_xy_error_std (gamma 1.0 100.0)]

[assume fractional_heading_error_std (gamma 1.0 100.0)]

[assume additive_xy_error_std (gamma 1.0 100.0)]

[assume additive_heading_error_std (gamma 1.0 100.0)]

[assume initial_pose (list (uniform_continuous -1 1)
                           (uniform_continuous -1 1)
                           (uniform_continuous -1 1))]

[assume get_pose (mem (lambda (t)
  (if (= t 0) initial_pose
              (simulate_motion 1
                               (get_pose (- t 1))
                               constant_control
                               vehicle_params
                               fractional_xy_error_std
                               fractional_heading_error_std
                               additive_xy_error_std
                               additive_heading_error_std
                               ))))]

"""

program = program_constants + program_assumes


# ripl with NO observes
from_prior = sample_from_prior(N_steps, N_infer)

# ripl with observes
posterior_ripl = gen_ripl()
observe_gps = functools.partial(_observe_gps, posterior_ripl)
map(observe_gps, range(1, N_steps))
#
filename = base_filename + '_' + ('%04d' % 0) + '.png'
from_posterior = predict_from_ripl(posterior_ripl, N_steps)
plot(from_prior, from_posterior, filename)
#
step_by = 1
for idx in range(1, N_infer / step_by + 1):
    infer_str = gen_infer_str(N_steps, step_by)
    print infer_str
    posterior_ripl.infer(infer_str)
    from_posterior = predict_from_ripl(posterior_ripl, N_steps)
    filename = base_filename + '_' + ('%04d' % idx * step_by) + '.png'
    print filename
    plot(from_prior, from_posterior, filename)
    pass

