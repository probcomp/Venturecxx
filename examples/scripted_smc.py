import os
import argparse
#
import numpy
#
from venture.venturemagics.ip_parallel import MRipl
import vehicle_program as vp
import vehicle_simulator as vs


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


combined_frame = read_combined_frame()
mripl = MRipl(4, backend='puma')
mripl.execute_program(vp.program)

max_rows = 40
predictions = []
for ts, row in combined_frame.head(max_rows).iterrows():
    vp.do_assume_dt(mripl, row.i, row.dt)
    if not numpy.isnan(row.Velocity):
        vp.do_assume_control(mripl, row.i, row.Velocity, row.Steering)
        pass
    else:
        vp.do_assume_random_control(mripl, row.i)
        pass
    vp.do_assume_pose(mripl, row.i)
    if not numpy.isnan(row.x):
        vp.do_observe_gps(mripl, row.i, (row.x, row.y, row.heading))
        pass
    # do infers
    mripl.infer(vp.get_infer_args(row.i)[0])
    for _i in range(int(row.i))[-5:]:
        mripl.infer(vp.get_infer_args(_i)[1])
        pass
    prediction = mripl.predict(vp.pose_name_str % row.i)
    print prediction
    predictions.append(prediction)
    pass


