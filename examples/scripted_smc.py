import os
import argparse
#
import numpy
#
from venture.venturemagics.ip_parallel import MRipl
from venture.shortcuts import make_puma_church_prime_ripl
import vehicle_program as vp
import vehicle_simulator as vs
from contexts import Timer


def read_combined_frame():
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
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
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(dirname)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    return combined_frame
def get_row_iter(frame, N_rows=None):
    row_iter = None
    if N_rows is not None:
        row_iter = frame.head(N_rows).iterrows()
        pass
    else:
        row_iter = frame.iterrows()
        pass
    return row_iter
inspect_parameters_str = ' '.join([
    'additive_xy_error_std',
    'additive_heading_error_std',
    'fractional_xy_error_std',
    'fractional_heading_error_std',
    'gps_xy_error_std',
    'gps_heading_error_std',
    ])
def inspect_vars(ripl, _i=None):
    predict_mean = lambda x: numpy.array(ripl.predict(x)).mean(axis=0)
    predict_std = lambda x: numpy.array(ripl.predict(x)).std(axis=0)
    if _i is None:
        _i = row.i
        pass
    predict_str_and_func = [
            ('pose_%d' % _i, predict_mean),
            ('pose_%d' % _i, predict_std),
            ('control_%d' % _i, predict_mean),
            ('(list %s)' % inspect_parameters_str, predict_mean),
            ]
    for predict_str, func in predict_str_and_func:
        print predict_str
        print func(predict_str)
        pass
    pass


combined_frame = read_combined_frame()
#ripl = MRipl(no_ripls=64, backend='puma')
ripl = make_puma_church_prime_ripl()
ripl.execute_program(vp.program)
ripl.observe('(normal gps_xy_error_std 0.01)', 0)
ripl.observe('(normal gps_heading_error_std 0.01)', 0)
ripl.observe('(normal (lookup pose_0 0) 0.1)', combined_frame.irow(0).x)
ripl.observe('(normal (lookup pose_0 1) 0.1)', combined_frame.irow(0).y)
ripl.observe('(normal (lookup pose_0 2) 0.1)', combined_frame.irow(0).heading)
out = ripl.infer('(mh default all 100)')
out = ripl.infer('(mh latents all 100)')


def infer_N_history(ripl, _i, N_history):
    _is = range(int(_i))[-N_history:]
    for _i in _is:
        ripl.infer(vp.get_infer_args(_i)[1])
        pass
    return
N_history = 13
N_hypers_profile = 31
def process_row(ripl, row, predictions=None):
    # dt
    vp.do_assume_dt(ripl, row.i, row.dt)
    # control
    if not numpy.isnan(row.Velocity):
        vp.do_assume_control(ripl, row.i, row.Velocity, row.Steering)
        pass
    else:
        vp.do_assume_random_control(ripl, row.i)
        ripl.observe('(normal (lookup control_%d 0) 0.1)' % row.i, 0)
        ripl.observe('(normal (lookup control_%d 1) 0.1)' % row.i, 0)
        pass
    # pose
    vp.do_assume_pose(ripl, row.i)
    # gps
    if not numpy.isnan(row.x):
        vp.do_observe_gps(ripl, row.i, (row.x, row.y, row.heading))
        pass
    # do infers
    if row.i < N_hypers_profile:
        ripl.infer(vp.get_infer_args(row.i)[0])
        pass
    infer_N_history(ripl, row.i, N_history)
    prediction = ripl.predict(vp.get_pose_name_str(row.i))
    if predictions is not None:
        predictions.append(prediction)
        pass
    return prediction


if False:
    times = []
    N_rows = 13
    with Timer('all rows') as t_outer:
        for ts, row in get_row_iter(combined_frame, N_rows):
            with Timer('row %s' % row.i) as t_inner:
                prediction = process_row(ripl, row, predictions)
                pass
            times.append(t_inner.elapsed)
            pass
        pass

    map(lambda x: inspect_vars(ripl, x), range(N_rows))

#process_row(ripl, combined_frame.irow(0))
#out = map(ripl.infer, vp.get_infer_args(0))
#inspect_vars(ripl, 0)
#
#process_row(ripl, combined_frame.irow(1))
#out = map(ripl.infer, vp.get_infer_args(1))
#inspect_vars(ripl, 1)
