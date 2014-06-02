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
    get_mean = lambda x: x if len(x.shape) == 1 else x.mean(axis=0)
    get_std = lambda x: x if len(x.shape) == 1 else x.std(axis=0)
    if _i is None:
        _i = row.i
        pass
    predict_str_and_func = [
            ('pose_%d' % _i, get_mean),
            ('pose_%d' % _i, get_std),
            ('control_%d' % _i, get_mean),
            ('(list %s)' % inspect_parameters_str, get_mean),
            ('(list %s)' % inspect_parameters_str, get_std),
            ]
    for predict_str, func in predict_str_and_func:
        value = numpy.array(ripl.predict(predict_str))
        func_value = func(value)
        print predict_str
        print func_value
        pass
    print
    pass


combined_frame = read_combined_frame()
ripl = MRipl(no_ripls=64, backend='puma')
#ripl = make_puma_church_prime_ripl()
ripl.execute_program(vp.program)
ripl.observe('(normal gps_xy_error_std 0.01)', 0)
ripl.observe('(normal gps_heading_error_std 0.01)', 0)
ripl.observe('(normal (lookup pose_0 0) 0.1)', combined_frame.irow(0).x)
ripl.observe('(normal (lookup pose_0 1) 0.1)', combined_frame.irow(0).y)
ripl.observe('(normal (lookup pose_0 2) 0.1)', combined_frame.irow(0).heading)
for _i in range(10):
    out = ripl.infer(vp.infer_state_str % 0)
    pass

def infer_N_history(ripl, _i, N_history):
    _is = range(int(_i))[-N_history:]
    for _i in _is:
        ripl.infer(vp.get_infer_args(_i)[1])
        pass
    return
N_history = 13
N_hypers_profile = 31
def process_row(ripl, row, predictions=None, verbose=True):
    is_control_row = not numpy.isnan(row.Velocity)
    is_gps_row = not numpy.isnan(row.x)
    is_infer_hypers_row = row.i < N_hypers_profile
    #
    vp.do_assume_dt(ripl, row.i, row.dt)
    if is_control_row
        vp.do_assume_control(ripl, row.i, row.Velocity, row.Steering)
        pass
    else:
        vp.do_assume_random_control(ripl, row.i)
        pass
    vp.do_assume_pose(ripl, row.i)
    if is_gps_row:
        vp.do_observe_gps(ripl, row.i, (row.x, row.y, row.heading))
        pass
    if is_infer_hypers_row:
        ripl.infer(vp.get_infer_args(row.i)[0])
        pass
    infer_N_history(ripl, row.i, N_history)
    if row.i < 4:
        for _i in range(9):
            infer_N_history(ripl, row.i, N_history)
            pass
        pass
    prediction = ripl.predict(vp.get_pose_name_str(row.i))
    if predictions is not None:
        predictions.append(prediction)
        pass
    if verbose:
        inspect_vars(ripl, row.i)
        pass
    return prediction


predictions = []
times = []
if True:
    N_rows = 24
    with Timer('all rows') as t_outer:
        for ts, row in get_row_iter(combined_frame, N_rows):
            with Timer('row %s' % row.i) as t_inner:
                prediction = process_row(ripl, row, predictions)
                pass
            times.append(t_inner.elapsed)
            pass
        pass
    pass
else:
    out = ripl.infer('(mh default one 100)')
    inspect_vars(ripl, 0)
    print "Done 0"
    print
    #
    row = combined_frame.irow(0)
    prediction = process_row(ripl, row, predictions)
    inspect_vars(ripl, 0)
    inspect_vars(ripl, 1)
    print "Done 1"
    print
    #
    row = combined_frame.irow(1)
    prediction = process_row(ripl, row, predictions)
    inspect_vars(ripl, 0)
    inspect_vars(ripl, 1)
    inspect_vars(ripl, 2)
    print "Done 2"
    print

# map(lambda x: inspect_vars(ripl, x), range(N_rows))

#process_row(ripl, combined_frame.irow(0))
#out = map(ripl.infer, vp.get_infer_args(0))
#inspect_vars(ripl, 0)
#
#process_row(ripl, combined_frame.irow(1))
#out = map(ripl.infer, vp.get_infer_args(1))
#inspect_vars(ripl, 1)
