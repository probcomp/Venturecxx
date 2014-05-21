import numpy
#
from simulator import Simulator
import slamutils
from venture.shortcuts import make_puma_church_prime_ripl


N_steps = 40
N_infer = 10
vehicle_a=0.299541
vehicle_b=0.0500507
vehicle_h=0
vehicle_L=0.257717


simulate_motion_str = """
(simulate_motion
  (quote pose)
  (quote control)
  (quote dt)
  )
  """
simulate_laser_str = """
(simulate_laser
  (quote pose)
  (quote map)
  )
  """
simulate_gps_str = """
(simulate_gps
  (quote pose)
  )
  """

program_constants = """

[ASSUME vehicle_params (list %s %s %s %s)]

""" % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)

program_utils = """

"""

program_assumes = """

[ASSUME get_map (mem (lambda () (simulate_map)))]

[ASSUME get_control
  (mem (lambda (t)
    (list (uniform_continuous .5 1)
          (uniform_continuous -.01 .01))))]

[ASSUME get_pose
  (mem (lambda (t)
    (if (= t 0)
        (list 0 0 0)
        (simulate_motion .01
                         (get_pose (- t 1))
                         (get_control t)
                         vehicle_params
                         ))))]

"""

program = program_constants + program_utils + program_assumes


get_pose = lambda i: ripl.predict('(get_pose %s)' % i)
get_control = lambda i: ripl.predict('(get_control %s)' % i)
observe_control = lambda (i, control): ripl.observe('(get_control %s)' % i,
        _convert(control))
def read_data(dataset_name='5_eight'):
    import os
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
    dirname = os.path.join(base_dir, dataset_name, 'data')
    landmark_filename = 'obstacles.csv'
    control_filename = 'ground/slam_control.csv'
    gps_filename = 'ground/slam_gps.csv'
    sensor_filename = 'slam_sensor.csv'
    control_index_col = 'Time_VS'
    gps_index_col = 'TimeGPS'
    gps_to_target = dict(GPSLat='y', GPSLon='x', Orientation='heading')
    #
    gps_frame = slamutils.read_frame(gps_filename, dirname=dirname,
            index_col=gps_index_col, colname_map=gps_to_target)
    control_frame = slamutils.read_frame(control_filename, dirname=dirname,
            index_col=control_index_col)
    initial_state = slamutils.get_initial_state(gps_frame)
    return gps_frame, control_frame, initial_state
def _convert_real(val):
    return {"type":"real","value":val}
def _convert_list(val):
    return {"type":"vector","value":map(_convert, val)}
def _convert(val):
    is_list = isinstance(val, (list, tuple))
    val = _convert_list(val) if is_list else _convert_real(val)
    return val
gps_frame, control_frame, initial_state = read_data()


ripl = make_puma_church_prime_ripl()
ripl.execute_program(program)
world = ripl.predict('(get_map)')
poses = numpy.array(map(get_pose, range(N_steps)))
controls = numpy.array(map(get_control, range(N_steps)))
ripl.infer(N_infer)
if True:
    poses = numpy.array(map(get_pose, range(N_steps)))
    controls = numpy.array(map(get_control, range(N_steps)))

if False:
    for varname in ['world', 'poses', 'controls']:
        print '%s:\n%s\n' % (varname, locals()[varname])
        pass

import pylab
pylab.ion()
pylab.show()
pylab.figure()
pylab.subplot(211)
pylab.plot(poses[:, 0], poses[:, 1])
pylab.subplot(212)
pylab.plot(poses[:, 2])
