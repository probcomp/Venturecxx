import matplotlib
matplotlib.use('Agg')
#
import os
import sys
import argparse
#
import numpy as np
import numpy.random as npr
import pandas
from matplotlib import pyplot as plt
from IPython.core.debugger import Pdb
#
import venture.shortcuts
import scene_plot_utils as spu
import vehicle_simulator as vs
from contexts import Timer


def parse_args(args_override=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', type=str)
    parser.add_argument('output_dir', type=str)
    parser.add_argument('--max_time', type=float, default=None)
    parser.add_argument('--clean_dir', type=str, default=None)
    parser.add_argument('--dataset_name', type=str, default='')
    parser.add_argument('--ground', action='store_true')
    parser.add_argument('--version', default='random_walk')
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--frames', type=int, default=100000)
    parser.add_argument('--samples', type=int, default=10)
    parser.add_argument('--window_size', type=int, default=10)
    args = parser.parse_args(args_override)
    return args

def set_trace():
    Pdb(color_scheme='LightBG').set_trace(sys._getframe().f_back)

# Read and pre-process the data.
def read_combined_frame(args):
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(args.input_dir)
    combined_frame = vs.combine_frames(control_frame, gps_frame)

    gps_to_clean_gps = dict(GPSLat='clean_y', GPSLon='clean_x', Orientation='clean_heading')
    clean_gps_frame = pandas.DataFrame(columns=gps_to_clean_gps.values())
    if args.clean_dir is not None:
        clean_gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
            colname_map=gps_to_clean_gps)
        clean_gps_frame = vs.read_frame(dirname=args.clean_dir, **clean_gps_frame_config)

    combined_frame = combined_frame.join(clean_gps_frame)
    combined_frame = combined_frame.truncate(after=args.max_time)
    combined_frame = combined_frame.head(args.frames)

    return combined_frame

# Plot samples along with the ground truth.
def plot_pose(figname, xlim, ylim, xs=None, ys=None, headings=None, clean_gps_pose=None):
    with Timer(figname) as t:
        # set_trace()
        spu.plot_scene_scatter(xs, ys, headings, clean_gps_pose)
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.savefig(figname, format = 'png')
        plt.close()
        pass
    return

def make_movie(dataset_name):
    # Make the mp4 movie.
    mp4_name = dataset_name + '.mp4'
    template_str = dataset_name + '_raw_%1d.png'
    os.system('avconv -y -r 15 -i %s %s' % (template_str, mp4_name))
    return

def ensure(path):
    path = path[:path.rfind('/')]
    if not os.path.exists(path):
        os.makedirs(path)

def writeCSV(filename, cols, rows):
    ensure(filename)
    with open(filename, 'w') as f:
        f.write(','.join(cols) + '\n')
        for row in rows:
            f.write(','.join(map(str, row)) + '\n')

def write_landmarks_file(output_dir, landmarks_data=((0,0),)):
    landmarks_file = '%s/slam_out_landmarks.csv' % output_dir
    landmarks_cols = ['SLAMBeaconX','SLAMBeaconY']
    writeCSV(landmarks_file, landmarks_cols, landmarks_data)
    print "Wrote landmarks data to " + landmarks_file
    return

def write_path_file(output_dir, path_data):
    filename = '%s/slam_out_path.csv' % output_dir
    column_names = ['SLAMGPSTime', 'SLAMLat', 'SLAMLon']
    writeCSV(filename, column_names, path_data)
    print "Wrote path data to " + filename
    return

def get_clean_gps(row):
    return (row['clean_x'], row['clean_y'], row['clean_heading'])

# Run the simple random walk solution.
def runRandomWalk():

    # Parameters for the random walk prior with Gaussian steps.
    noisy_gps_stds = dict(x=0.05, y=0.05, heading=0.01)

    ripl = venture.shortcuts.make_church_prime_ripl()

    print "Using %d row" % len(combined_frame)
    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []
    out_rows = []
    gps_frame_count = 0

  # For each row...
    for row_i, (_T, combined_frame_row) in enumerate(combined_frame.iterrows()):
        with Timer('row %s' % row_i) as t:
            # set_trace()
            clean_gps = get_clean_gps(combined_frame_row)
                  
            xs = []
            ys = []
            headings = []
          
            # generate the samples
            for k in range(N_samples):
                ripl.clear()
              
                if row_i is 0:
                    ripl.assume("x", "(normal 0 1)")
                    ripl.assume("y", "(normal 0 1)")
                    ripl.assume("heading", "(uniform_continuous -3.14 3.14)")
                else:
                    ripl.assume("x", "(normal %f 0.1)" % prev_x)
                    ripl.assume("y", "(normal %f 0.1)" % prev_y)
                    ripl.assume("heading", "(normal %f 0.1)" % prev_heading)
              
                # we have noisy gps observations, let's condition on them!
                if not np.isnan(combined_frame_row['x']):
                    noisy_gps_x = combined_frame_row['x']
                    noisy_gps_y = combined_frame_row['y']
                    noisy_gps_heading = combined_frame_row['heading']
                  
                    ripl.observe("(normal x %f)" % noisy_gps_stds['x'], noisy_gps_x)
                    ripl.observe("(normal y %f)" % noisy_gps_stds['y'], noisy_gps_y)
                    #ripl.observe("(normal heading %f)" % noisy_gps_stds['heading'], noisy_gps_heading)
                  
                    ripl.infer("(slice default one 20)")

                xs.append(float(ripl.sample("x")))
                ys.append(float(ripl.sample("y")))
                headings.append(float(ripl.sample("heading")))

            xs = np.array(xs)
            ys = np.array(ys)
            headings = np.array(headings)
            prev_x = xs.mean()
            prev_y = ys.mean()
            prev_heading = headings.mean()
          
            # if the frame has gps signal, plot it
            if not np.isnan(combined_frame_row['x']):
                gps_frame_count += 1
                if args.plot:
                    filename = dataset_name + "_raw_%s.png" % gps_frame_count
                    plot_pose(filename, xlim, ylim, xs=xs, ys=ys,
                            headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
      
        times.append(t.elapsed)

    print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
    if args.plot:
        make_movie(dataset_name)

    return out_rows, ripl

def runApproach2():
    '''
    Run approach 2 as outlined in the document
    '''
    # Parameters for the random walk prior with Gaussian steps.
    noisy_gps_stds = dict(heading=0.01)
    k = args.window_size
  
    ripl = venture.shortcuts.make_church_prime_ripl()

    print "Using %d row" % len(combined_frame)
    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []
    out_rows = []
    gps_frame_count = 0
    def assume_T_0():
        # make model assumptions
        ripl.assume("x0", "(scope_include 0 0 (normal -6.1 1))", label="lx0")
        ripl.assume("y0", "(scope_include 0 1 (normal -.05 1))", label="ly0")
        ripl.assume("noisy_gps_x_std",
                "(scope_include (quote parameters) 0 (gamma 1 100))")
        ripl.assume("noisy_gps_y_std",
                "(scope_include (quote parameters) 1 (gamma 1 100))")
        ripl.assume("heading0", "(uniform_continuous -3.14 3.14)",
                "lh0")
        return
    def assume_T(T):
        print 'assume_T(%i)' % T
        # assume x value given previous state
        ripl.assume("x%i"%T,
                "(scope_include %i 0 (normal x%i 0.03))" % (T, T-1),
                "lx%i"%T)
        ripl.assume("y%i"%T,
                "(scope_include %i 1 (normal y%i 0.003))" % (T, T-1),
                "ly%i"%T)
        ripl.assume("heading%i"%T, "(normal heading%i 0.1)" % (T-1,),
                "lh%i"%T)
        return
    def freeze_assumes(T_minus_k_plus_1):
        print 'freeze_assumes(%i)' % T_minus_k_plus_1
        symbols = ['lx%i', 'ly%i', 'lh%i']
        symbols = [symbol % T_minus_k_plus_1 for symbol in symbols]
        map(ripl.freeze, symbols)
        return
    def forget_assumes(T_minus_k):
        print 'forget_assumes(%i)' % T_minus_k
        symbols = ['lx%i', 'ly%i', 'lh%i']
        symbols = [symbol % T_minus_k for symbol in symbols]
        map(ripl.forget, symbols)
        return
    def forget_data(T_minus_k_plus_1):
        print 'forget_data(%i)' % T_minus_k_plus_1
        symbols = ['x_data%i', 'y_data%i']
        symbols = [symbol % T_minus_k_plus_1 for symbol in symbols]
        map(ripl.forget, symbols)
        return
    def observe_gps(row):
        print 'observe_gps(row.i=%i)' % row.i
        noisy_gps_x = row['x']
        noisy_gps_y = row['y']
        noisy_gps_heading = row['heading']
        print 'time: ', row.name
        print "NOISY: " + str((noisy_gps_x, noisy_gps_y, noisy_gps_heading))

        ripl.observe("(normal x%i noisy_gps_x_std)"%T, noisy_gps_x, label="x_data%i"%T )
        ripl.observe("(normal y%i noisy_gps_y_std)"%T, noisy_gps_y, label="y_data%i"%T)
        #ripl.observe("(normal heading %f)" % noisy_gps_stds['heading'], noisy_gps_heading)
        return
    infer_on_scope = lambda type, T: "(%s %i one 50)" % (type, T)
    def get_infer_str(T, k, type='mh'):
        Ts = range(T+1)[-k+2:]
        _infer_on_scope = lambda T: infer_on_scope(type, T)
        infer_on_scopes = map(_infer_on_scope, Ts)
        forward_infer = ' '.join(infer_on_scopes)
        backward_infer = ' '.join(infer_on_scopes[::-1])
        make_cycle = lambda infer_strs, N: "(cycle (%s) %i)" % (' '.join(infer_strs), N)
        infer_strs = (backward_infer, forward_infer)
        cycle_on_Ts = make_cycle(infer_strs, 1)
        return cycle_on_Ts
    def infer(T, k, type):
        infer_str = get_infer_str(T, k, type)
        print 'infer_str: %s' % infer_str
        ripl.infer(infer_str)
        if T < 100:
            ripl.infer('(mh parameters one 1000)')
        return
    for T, (_T, combined_frame_row) in enumerate(combined_frame.iterrows()):
        with Timer('row %s' % T) as t:
            clean_gps = get_clean_gps(combined_frame_row)

            was_gps_row = not np.isnan(combined_frame.irow(T-k+1)['x'])
            is_gps_row = not np.isnan(combined_frame_row['x'])
            if T == 0:
                assume_T_0()
            else:
                assume_T(T)
                # set_trace()
                if T >= (k - 1):
                    freeze_assumes(T - k + 1)
                    # forget the observations if they exist
                    if was_gps_row:
                        forget_data(T - k + 1)
                if T >= k:
                    forget_assumes(T - k)

                # print ripl.list_directives()[-5:],'\n'

            # we have noisy gps observations, let's condition on them!
            if is_gps_row:
                observe_gps(combined_frame_row)
                infer(T, k, 'mh')
            else:
                # # Don't need to run infernece here
                # infer_str = infer_on_scope('mh', T)
                # ripl.infer(infer_str)
                pass

            xs = np.array([float(ripl.sample("x%i"%T))])
            ys = np.array([float(ripl.sample("y%i"%T))])
            headings = np.array([float(ripl.sample("heading%i"%T))])
            print '\n xs:',xs,'ys',ys,'\n'

            # if the frame has gps signal, plot it
            if is_gps_row:
                gps_frame_count += 1
                if args.plot:
                    filename = dataset_name + "_raw_%s.png" % gps_frame_count
                    plot_pose(filename, xlim, ylim, xs=xs, ys=ys,
                              headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
      
        times.append(t.elapsed)

    print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
    if args.plot:
        make_movie(dataset_name)

    return out_rows, ripl

def runApproach3():
    '''
    run approach 3 as outlined in doc
    '''
    # Parameters for the random walk prior with Gaussian steps.
    k = args.window_size
    ripl = venture.shortcuts.make_church_prime_ripl()
    print "Using %d row" % len(combined_frame)
    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []
    out_rows = []
    gps_frame_count = 0
    for T, (_T, combined_frame_row) in enumerate(combined_frame.iterrows()):
        with Timer('row %s' % T) as t:
            clean_gps = get_clean_gps(combined_frame_row)
            xs = []
            ys = []
            headings = []
            x_datas = []
            y_datas = []

            if T is 0:
                # assumes on model parameters; put them in their own scope
                ripl.assume("noisy_gps_x_std", "(gamma 1 20)")
                ripl.assume("noisy_gps_y_std", "(gamma 1 20)")
                ripl.assume("noisy_motion_heading_std", "(gamma 1 1)")
                ripl.assume("noisy_motion_x_std", "(gamma 1 1)")
                ripl.assume("noisy_motion_y_std", "(gamma 1 1)")

                # intial position
                ripl.assume("x0", "(normal 0 1)", label="lx0")
                ripl.assume("y0", "(normal 0 1)", label="ly0")
                # initial heading
                ripl.assume("heading0", "(uniform_continuous -3.14 3.14)",
                            label = "lh0")

            else:
                # grab steering, velocity, heading
                control_steer = combined_frame_row['Steering']
                if np.isnan(control_steer): control_steer = 0
                control_velocity = combined_frame_row['Velocity']
                if np.isnan(control_velocity): control_velocity = 0
                dt = combined_frame_row['dt']
                # assume heading
                heading_assume = ('(normal (+ (* %f %f) heading%i) noisy_motion_heading_std)' 
                                  % (dt, control_steer, T-1))
                ripl.assume("heading%i"%T, heading_assume, "lh%i"%T)
                # x and y
                linearized_offset = dt * control_velocity
                x_assume = ('(normal (+ (* %f (cos heading%i))) noisy_motion_x_std)' 
                            % (linearized_offset, T-1))
                ripl.assume("x%i"%T, x_assume, "lx%i"%T)
                y_assume = ('(normal (+ (* %f (sin heading%i))) noisy_motion_y_std)' 
                            % (linearized_offset, T-1))
                ripl.assume("y%i"%T, y_assume, "ly%i"%T)

                if T >= (k - 1):
                    ripl.freeze("lx%i"%(T-k+1))
                    ripl.freeze("ly%i"%(T-k+1))
                    ripl.freeze("lh%i"%(T-k+1))
                    # forget the observations if they exist
                    if not np.isnan(combined_frame.irow(T-k+1)['x']):
                        ripl.forget("x_data%i"%(T-k+1))
                        ripl.forget("y_data%i"%(T-k+1))

                if T >= k:
                    ripl.forget("lx%i"%(T-k))
                    ripl.forget("ly%i"%(T-k))
                    ripl.forget("lh%i"%(T-k))

                # print ripl.list_directives()[-5:],'\n'

            # we have noisy gps observations, let's condition on them!
            if not np.isnan(combined_frame_row['x']):
                noisy_gps_x = combined_frame_row['x']
                noisy_gps_y = combined_frame_row['y']
                noisy_gps_heading = combined_frame_row['heading']
                print 'time: ',T
                print "NOISY: " + str((noisy_gps_x, noisy_gps_y, noisy_gps_heading))

                ripl.observe("(normal x%i noisy_gps_x_std)"%T, noisy_gps_x, label="x_data%i"%T )
                ripl.observe("(normal y%i noisy_gps_y_std)"%T, noisy_gps_y, label="y_data%i"%T)
                #ripl.observe("(normal heading %f)" % noisy_gps_stds['heading'], noisy_gps_heading)

                ripl.infer("(slice default one 50)")

            xs.append(float(ripl.sample("x%i"%T)))
            ys.append(float(ripl.sample("y%i"%T)))
            headings.append(float(ripl.sample("heading%i"%T)))

            xs = np.array(xs)
            ys = np.array(ys)
            headings = np.array(headings)

            print '\n xs:',xs,'ys',ys,'\n'

            # if the frame has gps signal, plot it
            if not np.isnan(combined_frame_row['x']):
                gps_frame_count += 1
                if args.plot:
                    filename = dataset_name + "_raw_%s.png" % gps_frame_count
                    plot_pose(filename, xlim, ylim, xs=xs, ys=ys,
                              headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
      
        times.append(t.elapsed)

    if args.plot:
        make_movie(dataset_name)

    return out_rows, ripl


if __name__ == '__main__':
    args = parse_args()
    # set_trace()
    dataset_name = args.dataset_name

    print "Loading data"
    combined_frame = read_combined_frame(args)

    xlim = (-10, 10)
    ylim = (-5, 5)
    print "Set plot limits: " + str((xlim, ylim))

    approaches = dict(random_walk = runRandomWalk,
                      version_2 = runApproach2,
                      version_3 = runApproach3)
    approach = approaches[args.version]
    out_rows, ripl = approach()

    write_path_file(args.output_dir, out_rows)
    landmarks_data=((0,0),)
    write_landmarks_file(args.output_dir, landmarks_data)
