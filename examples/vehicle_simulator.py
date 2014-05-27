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
    dts = numpy.append([first_dt], numpy.diff(list(frame.index)))
    return dts

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
def propagate_left(left_frame, right_frame):
    padded = left_frame.join(right_frame, how='outer').fillna(method='pad')
    padded = padded.reindex(columns=left_frame.columns)
    return padded.join(right_frame)
def combine_frames(control_frame, gps_frame):
    frame = propagate_left(control_frame, gps_frame)
    frame = insert_dts(frame)
    return frame
def xs_to_control_observes(i, xs):
    observes = []
    if not numpy.isnan(xs.Velocity):
        observes = [
                    (vp.get_control_str % (i, 0), xs.Velocity),
                    (vp.get_control_str % (i, 1), xs.Steering),
                    ]
    return observes
def xs_to_gps_observes(i, xs):
    observes = []
    if not numpy.isnan(xs.x):
        observe_str = vp.simulate_gps_str % i
        observe_val = _convert((xs.x, xs.y, xs.heading))
        observes = [(observe_str, observe_val), ]
    return observes
def xs_to_dt_observes(i, xs):
    observes = [(vp.sample_dt_str % i, xs.dt), ]
    return observes
def xs_to_all_observes((i, (t, xs))):
    control_observes = xs_to_control_observes(i, xs)
    gps_observes = xs_to_gps_observes(i, xs)
    dt_observes = xs_to_dt_observes(i, xs)
    all_observes = control_observes + gps_observes + dt_observes
    return all_observes
def frames_to_all_observes(control_frame, gps_frame):
    combined = combine_frames(control_frame, gps_frame)
    ts = list(combined.index)
    all_observes = map(xs_to_all_observes, enumerate(combined.iterrows()))
    return all_observes, ts

def create_sample_strs(ts):
    _is = range(len(ts))
    create_sample_str = lambda i: (vp.sample_pose_str % i,)
    return map(create_sample_str, _is)

def create_observe_sample_strs_lists(gps_frame, control_frame, N_timesteps=None):
    observe_strs_list, ts = frames_to_all_observes(control_frame, gps_frame)
    sample_strs_list = create_sample_strs(ts)
    observe_strs_list, sample_strs_list = \
            observe_strs_list[:N_timesteps], sample_strs_list[:N_timesteps]
    return observe_strs_list, sample_strs_list

def create_vehicle_simulator(dirname, program, N_mripls, backend,
        infer_args, N_timesteps=None):
    gps_frame, control_frame, laser_frame, sensor_frame = read_frames(dirname)
    observe_strs_list, sample_strs_list = create_observe_sample_strs_lists(
            gps_frame, control_frame, N_timesteps)
    # create/pass diagnostics functions?
    simulator = Simulator(program, observe_strs_list, sample_strs_list,
            N_mripls, backend, infer_args)
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
            vp.backend, vp.infer_args)
    samples = []
    for _i in range(40):
        print _i
        _samples_i = simulator.step(N=1)
        samples += map(lambda x: numpy.array(x).T, _samples_i)
        pass
    pass
