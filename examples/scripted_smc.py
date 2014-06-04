import os
import argparse
import collections
import multiprocessing
#
import numpy
import pylab
#
from venture.venturemagics.ip_parallel import MRipl
from venture.shortcuts import make_puma_church_prime_ripl
import scene_plot_utils as spu
import vehicle_program as vp
import vehicle_simulator as vs
from contexts import Timer


get_default_lim = lambda: ((-10, 10),(-10, 10))
lim_lookup = collections.defaultdict(get_default_lim, {
    '1_straight':((-7.0, 5.0),(-1.0, 1.0)),
    '2_bend':((-7.0, 1.0),(-1.0, 6.0)),
    #'3_curvy':((-7.0, 5.0),(-3.0, 1.0)),
    '4_circle':((-4.0, 4.0),(-4.0, 4.0)),
    '5_eight':((-2.5, 2.5),(-5.0, 2.0)),
    })
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
    clean_dirname = os.path.join(base_dir, dataset_name, 'data', 'ground')
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(dirname)
    clean_gps_frame = vs.read_frame(dirname=clean_dirname, **vs.gps_frame_config)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    return combined_frame, clean_gps_frame, dataset_name

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

def get_prefixed_expressions(ripl, prefix, instruction='predict'):
    is_this_instruction = lambda directive: directive['instruction'] == instruction
    def is_prefixed_directive(directive):
        expression = directive['expression']
        return isinstance(expression, str) and expression.startswith(prefix)
    get_expression = lambda directive: directive['expression']
    #
    directives = ripl.list_directives()
    filtered_directives = filter(is_this_instruction, directives)
    prefixed_directives = filter(is_prefixed_directive, filtered_directives)
    prefixed_expressions = map(get_expression, prefixed_directives)
    return list(set(prefixed_expressions))

def plot_pose((figname, (pose, clean_gps_pose))):
    with Timer(figname) as t:
        x, y, heading = map(numpy.array, zip(*pose))
        spu.plot_scene_scatter(x, y, heading, clean_gps_pose)
        pylab.gca().set_xlim(xlim)
        pylab.gca().set_ylim(ylim)
        pylab.savefig(figname)
        pylab.close()
        pass
    return

def plot_poses(pose_dict):
    pool = multiprocessing.Pool()
    with Timer('all plots') as t:
        #map(plot_pose, pose_dict.iteritems())
        pool.map(plot_pose, pose_dict.iteritems())
        pass
    return

def generate_pose_names(_is):
    generate_pose_name = lambda i: 'pose_' + str(i)
    return map(generate_pose_name, _is)

def get_logscores_and_poses(ripl, row_i):
    logscores = ripl.get_global_logscore()
    final_poses = ripl.predict('pose_%d' % row_i)
    cmp_on_logscore = lambda x, y: cmp(x[0], y[0])
    logscores_and_poses = sorted(zip(logscores, final_poses), cmp=cmp_on_logscore)
    return logscores_and_poses

def get_clean_gps_poses(_is, combined_frame, clean_gps_frame):
    def get_clean_gps_pose(_ix):
        xs = clean_gps_frame.ix[_ix]
        return (xs.x, xs.y, xs.heading)
    i_to_ix = dict(zip(combined_frame.i, combined_frame.index))
    indices = map(i_to_ix.get, _is)
    clean_gps_poses = map(get_clean_gps_pose, indices)
    return clean_gps_poses


combined_frame, clean_gps_frame, dataset_name = read_combined_frame()
def get_lims(clean_gps_frame):
    min_xs = clean_gps_frame.min()
    max_xs = clean_gps_frame.max()
    min_x, max_x = min_xs.x, max_xs.x
    min_y, max_y = min_xs.y, max_xs.y
    delta_x = (max_x - min_x) * .05
    delta_y = (max_y - min_y) * .05
    xlim = (min_x - delta_x, max_x + delta_x)
    ylim = (min_y - delta_y, max_y + delta_y)
    return xlim, ylim

xlim, ylim = get_lims(clean_gps_frame)
ripl = get_ripl(vp.program, combined_frame, vp.N_mripls, vp.backend,
        vp.use_mripl)
#
times = []
# row_is = range(len(combined_frame))
row_is = range(100)
gps_is = []
for row_i in row_is:
    with Timer('row %s' % row_i) as t:
        _i = process_row(ripl, combined_frame.irow(row_i))
        gps_is.append(_i)
        pass
    times.append(t.elapsed)
    pass
print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))


#pose_names = get_predicted_pose_names(ripl)
gps_is = map(int, filter(None, gps_is))
pose_names = generate_pose_names(gps_is)
with Timer('predicts') as t:
    poses = map(ripl.predict, pose_names)
    pass
# generate plots
override_pose_names = generate_pose_names(range(len(pose_names)))
override_pose_names = [dataset_name + '_' + x for x in override_pose_names]
clean_gps_poses = get_clean_gps_poses(gps_is, combined_frame, clean_gps_frame)
pose_dict = dict(zip(override_pose_names, zip(poses, clean_gps_poses)))
plot_poses(pose_dict)
# generate movie
mp4_name = dataset_name + '.mp4'
template_str = dataset_name + '_pose_%1d.png'
os.system('avconv -y -r 60 -b 1800 -i %s %s' % (template_str, mp4_name))

print '\n'.join(map(str, map(lambda x: numpy.array(x).mean(axis=0), poses)))
