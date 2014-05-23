import functools
#
import numpy
import pylab
pylab.ion()
pylab.show()
#
from venture.venturemagics.ip_parallel import MRipl


def _convert_real(val):
    return {"type":"real","value":val}
def _convert_list(val):
    return {"type":"vector","value":map(_convert, val)}
def _convert(val):
    is_list = isinstance(val, (list, tuple))
    val = _convert_list(val) if is_list else _convert_real(val)
    return val
get_predict = lambda ripl, x: ripl.predict('(get_pose %s)' % x)


vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717
#
constant_velocity = .1
constant_steering = 0
gps_heading = 0
gen_gps = lambda t: _convert((constant_velocity * t, 0, gps_heading))
#
N_mripls = 4
N_particles = 30
backend = 'puma'
N_infer = 200
N_steps = 10
predict_which = 0


program_constants = """

[assume vehicle_params (list %s %s %s %s)]

[assume constant_control (list %s %s)]

""" % (
        vehicle_a, vehicle_b, vehicle_h, vehicle_L,
        constant_velocity, constant_steering,
#        fractional_xy_error_std,
#        fractional_heading_error_std,
#        additive_xy_error_std,
#        additive_heading_error_std,
        )

program_assumes = """

[assume fractional_xy_error_std (gamma 1.0 100.0)]

[assume fractional_heading_error_std (gamma 1.0 100.0)]

[assume additive_xy_error_std (gamma 1.0 100.0)]

[assume additive_heading_error_std (gamma 1.0 100.0)]

[assume get_pose (mem (lambda (t)
  (if (= t 0) (list (uniform_continuous -1 1)
                    (uniform_continuous -1 1)
                    (uniform_continuous -1 1))
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
ripl0 = MRipl(N_mripls, backend=backend)
ripl0.execute_program(program)
ripl0.infer(N_infer)
get_predict0 = functools.partial(get_predict, ripl0)
predicts0 = numpy.array(map(get_predict0, range(N_steps)))

# ripl with observes
ripl1 = MRipl(N_mripls, backend=backend)
ripl1.execute_program(program)
for t in range(1, N_steps):
    ripl1.observe('(simulate_gps (get_pose %s) .1 .1)' % t, gen_gps(t))
    pass
#ripl1.infer(N_infer)
#ripl1.infer('(mh default one %s)' % N_infer)
ripl1.infer('(pgibbs default ordered %s %s)' % (N_particles, N_infer))
get_predict1 = functools.partial(get_predict, ripl1)
predicts1 = numpy.array(map(get_predict1, range(N_steps)))


pylab.figure()
for run_idx in range(predicts0.shape[1]):
    pylab.plot(predicts0[:, run_idx, 0], predicts0[:, run_idx, 1], 'r-x',
            alpha=0.2)
    pass
for run_idx in range(predicts1.shape[1]):
    pylab.plot(predicts1[:, run_idx, 0], predicts1[:, run_idx, 1], 'g-x',
            alpha=0.2)
    pass
pylab.savefig('vehicle_justs_gps.png')
