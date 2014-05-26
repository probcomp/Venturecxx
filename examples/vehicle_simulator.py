import os
import operator
#
import numpy
import pandas
#
from simulator import Simulator
import vehicle_program as vp


def read_frame(filename, dirname='', index_col=None, colname_map=None):
    full_filename = os.path.join(dirname, filename)
    frame = pandas.read_csv(full_filename, index_col=index_col)
    if colname_map is not None:
        frame = frame.rename(columns=colname_map)
        pass
    return frame

gps_to_target = dict(GPSLat='y', GPSLon='x', Orientation='heading')
gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
        colname_map=gps_to_target)
control_frame_config = dict(filename='slam_control.csv', index_col='Time_VS')
laser_frame_config = dict(filename='slam_laser.csv', index_col='TimeLaser')
def read_frames(dirname):
    gps_frame = read_frame(dirname=dirname, **gps_frame_config)
    control_frame = read_frame(dirname=dirname, **control_frame_config)
    laser_frame = read_frame(dirname=dirname, **laser_frame_config)
    return gps_frame, control_frame, laser_frame

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
                ('(dt %s)' % i, dt),
                ]
    dts = numpy.diff(list(control_frame.index))
    return [
            (t, single_control_to_observe_tuples(dt, i, control_xs))
            for (i, (dt, (t, control_xs))) in enumerate(zip(dts, control_frame.iterrows()))
            ]

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
    gps_frame, control_frame, laser_frame = read_frames(dirname)
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
    simulator.step()
    simulator.step()
    simulator.step()
    simulator.step()
