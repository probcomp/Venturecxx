import os
import operator
#
import numpy
import pandas
#
from simulator import Simulator
import vehicle_program as vp


def make_frame_dts(frame):
    first_dt = frame.index[0]
    return numpy.append([first_dt], numpy.diff(list(frame.index)))

def insert_dts(frame):
    frame = frame.copy()
    dts = make_frame_dts(frame)
    frame['dt'] = dts
    return frame

laser_sensor = 3
def postprocess_sensor_frame(frame):
    frame = frame.copy()
    frame = frame[frame.Sensor!=laser_sensor]
    frame = insert_dts(frame)
    return frame

def read_frame(filename, dirname='', index_col=None, colname_map=None,
        postprocess_func=None):
    full_filename = os.path.join(dirname, filename)
    frame = pandas.read_csv(full_filename, index_col=index_col)
    if colname_map is not None:
        frame = frame.rename(columns=colname_map)
        pass
    if postprocess_func is not None:
        frame = postprocess_func(frame)
    return frame

gps_to_target = dict(GPSLat='y', GPSLon='x', Orientation='heading')
gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
        colname_map=gps_to_target)
control_frame_config = dict(filename='slam_control.csv', index_col='Time_VS')
laser_frame_config = dict(filename='slam_laser.csv', index_col='TimeLaser')
sensor_frame_config = dict(filename='slam_sensor.csv', index_col='Time',
        postprocess_func=postprocess_sensor_frame)
def read_frames(dirname):
    gps_frame = read_frame(dirname=dirname, **gps_frame_config)
    control_frame = read_frame(dirname=dirname, **control_frame_config)
    laser_frame = read_frame(dirname=dirname, **laser_frame_config)
    sensor_frame = read_frame(dirname=dirname, **sensor_frame_config)
    return gps_frame, control_frame, laser_frame, sensor_frame


def my_xs(frame, t):
    eps = 1E-4
    xs = frame.truncate(before=t-eps, after=t+eps).irow(0)
    return xs
def _convert(val):
    def _convert_real(val):
        return {"type":"real","value":val}
    def _convert_list(val):
        return {"type":"vector","value":map(_convert, val)}
    is_list = isinstance(val, (list, tuple))
    return _convert_list(val) if is_list else _convert_real(val)
def generate_observes_for_gps_at_t(t, i, gps_frame):
    xs = my_xs(gps_frame, t)
    observe_str = vp.simulate_gps_str % i
    observe_val = _convert((xs.x, xs.y, xs.heading))
    observes = [(observe_str, observe_val), ]
    return observes
def generate_observes_for_control_at_t(t, i, control_frame):
    xs = my_xs(control_frame, t)
    observes = [
            (vp.get_control_str % (i, 0), xs.Velocity),
            (vp.get_control_str % (i, 1), xs.Steering),
            ]
    return observes
def modify_observes_for_control_at_i(i, control_observes):
    if len(control_observes) != 0:
        velocity = control_observes[0][1]
        steering = control_observes[0][1]
        control_observes = [
                (vp.get_control_str % (i, 0), velocity),
                (vp.get_control_str % (i, 1), steering),
                ]
    return control_observes
def generate_observes_for_dt_at_t(t, i, sensor_frame):
    xs = my_xs(sensor_frame, t)
    dt = xs.dt
    observes = [(vp.sample_dt_str % i, dt), ]
    return observes
def get_i(sensor_frame, t):
    # first i is never really observed, we only know the dt
    return sensor_frame.index.get_loc(t) + 1
sensor_to_key = {1:'gps', 2:'control', 3:'laser'}
def generate_observes_for_t(t, sensor_frame, last_control_observes,
        control_frame, gps_frame, **kwargs):
    sensor_xs = my_xs(sensor_frame, t)
    dt = sensor_xs.dt
    which_sensor = sensor_to_key[sensor_xs.Sensor]
    i = get_i(sensor_frame, t)
    if dt == t:
        # first sensor, if not control, don't add a control
        # observe a dt, but not a control
        # in addition, we always observe a dt for index 0
        # or perhaps, we always
        pass
    # not a special case
    control_observes, sensor_observes = [], []
    if which_sensor == 'control':
        control_observes = generate_observes_for_control_at_t(t, i,
                control_frame)
        sensor_observes = []
        pass
    else:
        control_observes = modify_observes_for_control_at_i(i, last_control_observes)
        if which_sensor == 'gps':
            sensor_observes = generate_observes_for_gps_at_t(t, i, gps_frame)
            pass
        else:
            assert False, 'uknown observe: %s' % which_sensor
            pass
        pass
    dt_observes = generate_observes_for_dt_at_t(t, i, sensor_frame)
    observes = dt_observes + control_observes + sensor_observes
    return observes, control_observes
def generate_all_observes(sensor_frame, control_frame, gps_frame):
    control_observes = []
    all_observes = []
    for i, t in enumerate(list(sensor_frame.index)):
        observes, control_observes = generate_observes_for_t(
                t, sensor_frame, control_observes, control_frame, gps_frame)
        all_observes.append(observes)
        pass
    return all_observes



def create_gps_observes(gps_frame):
    def _convert(val):
        def _convert_real(val):
            return {"type":"real","value":val}
        def _convert_list(val):
            return {"type":"vector","value":map(_convert, val)}
        is_list = isinstance(val, (list, tuple))
        return _convert_list(val) if is_list else _convert_real(val)
    def gps_xs_to_observe_tuple(gps_xs):
        time_as_float = gps_xs.name
        observe_str = vp.simulate_gps_str % time_as_float
        observe_val = (gps_xs.x, gps_xs.y, gps_xs.heading)
        observe_val = _convert(observe_val)
        return ((observe_str, observe_val), )
    process_tuple = lambda (t, xs): (t, gps_xs_to_observe_tuple(xs))
    return map(process_tuple, gps_frame.iterrows())

def create_control_observes(control_frame):
    def single_control_to_observe_tuples(dt, i, control_xs):
        return [
                ('(get_control_i %s 0)' % i, control_xs.Velocity),
                ('(get_control_i %s 1)' % i, control_xs.Steering),
                ('(get_dt_i %s)' % i, dt),
                ]
    first_dt = control_frame.index[0]
    dts = numpy.append([first_dt], numpy.diff(list(control_frame.index)))
    ret_list = [
            (t, single_control_to_observe_tuples(dt, i, control_xs))
            for (i, (dt, (t, control_xs))) in enumerate(zip(dts, control_frame.iterrows()))
            ]
    return ret_list

def create_sample_strs(ts):
    create_sample_str = lambda t: (vp.sample_pose_str % t,)
    return map(create_sample_str, ts)

def create_observe_sample_strs_lists(gps_frame, control_frame, N_timesteps=None):
    def interleave_observes(*args):
        all_observes = reduce(operator.add, map(list, args))
        my_cmp = lambda x, y: cmp(x[0], y[0])
        all_observes = sorted(all_observes, cmp=my_cmp)
        ts, observes = zip(*all_observes)
        return ts, observes
    gps_observes = create_gps_observes(gps_frame)
    control_observes = create_control_observes(control_frame)
    ts, observe_strs_list = interleave_observes(control_observes, gps_observes)
    sample_strs_list = create_sample_strs(ts)
    observe_strs_list, sample_strs_list = \
            observe_strs_list[:N_timesteps], sample_strs_list[:N_timesteps]
    return observe_strs_list, sample_strs_list

def create_vehicle_simulator(dirname, program, N_mripls, backend,
        N_infer, N_timesteps=None):
    gps_frame, control_frame, laser_frame, sensor_frame = read_frames(dirname)
    observe_strs_list, sample_strs_list = create_observe_sample_strs_lists(
            gps_frame, control_frame, N_timesteps)
    # create/pass diagnostics functions?
    simulator = Simulator(program, observe_strs_list, sample_strs_list,
            N_mripls, backend, N_infer)
    return simulator

if __name__ == '__main__':
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default=base_dir)
    parser.add_argument('--dataset_name', type=str, default='5_eight')
    parser.add_argument('--ground', action='store_true')
    args = parser.parse_args()
    base_dir = args.base_dir
    dataset_name = args.dataset_name
    use_noisy = not args.ground
    which_data = 'noisy' if use_noisy else 'ground'
    #
    dirname = os.path.join(base_dir, dataset_name, 'data', which_data)
    simulator = create_vehicle_simulator(dirname, vp.program, vp.N_mripls,
            vp.backend, vp.N_infer, N_timesteps=10)
    for _i in range(4):
        print _i
        print simulator.step()
        pass
    pass
