import os
import argparse
import collections
import multiprocessing
#
import numpy
import pylab
import pandas
#
from venture.venturemagics.ip_parallel import MRipl
from venture.shortcuts import make_puma_church_prime_ripl
import scene_plot_utils as spu
import vehicle_program as vp
import vehicle_simulator as vs
from contexts import Timer


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dirname', type=str)
    parser.add_argument('output_dirname', type=str)
    args = parser.parse_args()
    input_dirname = args.input_dirname
    output_dirname = args.output_dirname
    return input_dirname, output_dirname

def read_combined_frame(input_dirname):
    gps_frame, control_frame, laser_frame, sensor_frame = \
            vs.read_frames(input_dirname)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    return combined_frame, gps_frame

def infer_N_history(ripl, _i, N_history, N_infer=vp.N_infer, hypers=True):
    _is = range(int(_i))[-N_history:]
    map(ripl.infer, vp.get_infer_args(_is[0], N_infer, hypers))
    helper = lambda i: map(ripl.infer, vp.get_infer_args(i, N_infer, hypers=False))
    out = map(helper, _is[1:])
    return

N_hypers_profile = 80
N_history_gps = 13
N_history_not_gps = 1
to_assumes = []
def process_row(ripl, row):
    is_control_row = not numpy.isnan(row.Velocity)
    is_gps_row = not numpy.isnan(row.x)
    is_infer_hypers_row = row.i < N_hypers_profile
    N_history = N_history_gps if is_gps_row else N_history_not_gps
    N_infer = 30 if (row.i < 4) or is_gps_row else 20
    #
    global to_assumes
    to_assume = vp.get_assume_dt(row.i, row.dt)
    to_assumes.append(to_assume)
    to_assume = vp.get_assume_control(row.i, row.Velocity, row.Steering)
    to_assumes.append(to_assume)
    to_assume = vp.get_assume_pose(row.i)
    to_assumes.append(to_assume)
    if is_gps_row:
        to_assume_str = '\n'.join(to_assumes)
        to_assumes = []
        ripl.execute_program(to_assume_str)
        vp.do_observe_gps(ripl, row.i, (row.x, row.y, row.heading))
        infer_N_history(ripl, row.i, N_history, N_infer, hypers=is_infer_hypers_row)
        pass
    return row.i if is_gps_row else None

def process_frame(ripl, frame):
    gps_is = []
    for _, row in frame.iterrows():
        row_i = process_row(ripl, row)
        gps_is.append(row_i)
        pass
    gps_is = filter(None, gps_is)
    gps_is = map(int, gps_is)
    return gps_is

def get_ripl(program, combined_frame, N_mripls, backend, use_mripl):
    ripl = None
    if use_mripl:
        ripl = MRipl(no_ripls=N_mripls, backend=backend, set_no_engines=N_mripls)
        pass
    else:
        ripl = make_puma_church_prime_ripl()
        pass
    ripl.mr_set_seeds(range(vp.N_mripls))
    ripl.execute_program(program)
    ripl.observe('(normal gps_xy_error_std 0.01)', 0)
    ripl.observe('(normal gps_heading_error_std 0.01)', 0)
    ripl.observe('(normal (lookup pose_0 0) 0.1)', combined_frame.irow(0).x)
    ripl.observe('(normal (lookup pose_0 1) 0.1)', combined_frame.irow(0).y)
    ripl.observe('(normal (lookup pose_0 2) 0.1)', combined_frame.irow(0).heading)
    out = map(ripl.infer, vp.get_infer_args(0, 1000, False))
    return ripl

def generate_pose_names(_is):
    generate_pose_name = lambda i: 'pose_' + str(i)
    return map(generate_pose_name, _is)

def get_pose_names(ripl):
    directives = ripl.list_directives()
    get_symbol = lambda directive: directive['symbol'] if 'symbol' in directive else None
    def is_pose_directive(directive):
        expression = get_symbol(directive)
        return isinstance(expression, str) and expression.startswith('pose_')
    pose_directives = filter(is_pose_directive, directives)
    pose_names = map(get_symbol, pose_directives)
    return pose_names

def get_poses(ripl, gps_is):
    pose_names = generate_pose_names(gps_is)
    poses = map(ripl.predict, pose_names)
    poses = map(lambda x: numpy.array(x).mean(axis=0), poses)
    poses = numpy.array(poses)
    return poses

def write_output(poses, gps_frame, output_dirname):
    poses, ts = zip(*zip(poses, gps_frame.T))
    # futz with ordering: y, x
    poses = numpy.array(poses)[:, [1, 0]]
    column_names = 'SLAMLat', 'SLAMLon'
    frame = pandas.DataFrame(poses, index=ts, columns=column_names)
    frame.index.name = 'SLAMGPSTime'
    filename = os.path.join(output_dirname, 'slam_out_path.csv')
    frame.to_csv(filename)
    #
    landmark_frame = pandas.DataFrame([[0, 0]], columns=['SLAMBeaconX', 'SLAMBeaconY'])
    filename = os.path.join(output_dirname, 'slam_out_landmarks.csv')
    landmark_frame.to_csv(filename, index=False)
    # fixme
    return

input_dirname, output_dirname = parse_args()
combined_frame, gps_frame = read_combined_frame(input_dirname)
ripl = get_ripl(vp.program, combined_frame, vp.N_mripls, vp.backend,
        vp.use_mripl)
#
N_rows = 100
_gps_is = process_frame(ripl, combined_frame.head(N_rows))
poses = get_poses(ripl, _gps_is)
#
gps_is = combined_frame.reindex(gps_frame.index).i
N_gps = len(gps_is)
poses = numpy.vstack([poses, numpy.zeros((N_gps-len(poses),3))])
#
write_output(poses, gps_frame, output_dirname)
