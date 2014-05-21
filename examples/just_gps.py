import numpy
from venture.shortcuts import make_puma_church_prime_ripl


vehicle_a = 0.299541
vehicle_b = 0.0500507
vehicle_h = 0
vehicle_L = 0.257717


epsilon = .1 * 2 ** -2
N_predicts = 100
N_infer = 100


def _convert_real(val):
    return {"type":"real","value":val}
def _convert_list(val):
    return {"type":"vector","value":map(_convert, val)}
def _convert(val):
    is_list = isinstance(val, (list, tuple))
    val = _convert_list(val) if is_list else _convert_real(val)
    return val


program = """

[assume controls (list (list 0 0)
                       (list .1 .0)
                       (list .1 .0)
                       (list .1 .0)
                       (list .1 .0)
                       (list .1 0))]

[assume get_control (lambda (t) (lookup controls t))]

[assume vehicle_params (list %s %s %s %s)]

[assume get_pose (lambda (t)
  (if (= t 0) (list 0 0 0)
              (simulate_motion 1
                               (get_pose (- t 1))
                               (get_control (- t 1))
                               vehicle_params)))]

""" % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)


ripl0 = make_puma_church_prime_ripl()
ripl0.execute_program(program)
ripl0.infer(N_infer)
get_predict = lambda x: ripl0.predict('(get_pose %s)' % x)
predicts0 = numpy.array(map(get_predict, [4] * N_predicts))

ripl1 = make_puma_church_prime_ripl()
ripl1.execute_program(program)
heading = .01
ripl1.observe('(simulate_gps (get_pose 1))', _convert((0, 0, heading)))
ripl1.observe('(simulate_gps (get_pose 2))', _convert((.1+epsilon, 0, heading)))
ripl1.observe('(simulate_gps (get_pose 3))', _convert((.2+epsilon, 0, heading)))
ripl1.observe('(simulate_gps (get_pose 4))', _convert((.3+epsilon, 0, heading)))
ripl1.observe('(simulate_gps (get_pose 5))', _convert((.4+epsilon, 0, heading)))
ripl1.infer(N_infer)
ripl1.infer('(mh default one %s)' % N_infer)
get_predict = lambda x: ripl1.predict('(get_pose %s)' % x)
predicts1 = numpy.array(map(get_predict, [4] * N_predicts))

print 'predicts0.mean(axis=0):'
print predicts0.mean(axis=0)

print 'predicts1.mean(axis=0):'
print predicts1.mean(axis=0)

import pylab
pylab.ion()
pylab.show()
pylab.hist(predicts0[:, 0])
pylab.hist(predicts1[:, 0])
