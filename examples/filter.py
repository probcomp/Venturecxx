import matplotlib
from matplotlib import pyplot as plt
import argparse
import os
import venture.shortcuts
import scene_plot_utils as spu
import vehicle_simulator as vs

import numpy as np
import numpy.random as npr

from contexts import Timer

from IPython.core.debugger import Pdb
import sys

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
args = parser.parse_args()

def set_trace():
    Pdb(color_scheme='LightBG').set_trace(sys._getframe().f_back)

# Read and pre-process the data.
def read_combined_frame():
    dataset_name = args.dataset_name
    use_noisy = not args.ground
    which_data = 'noisy' if use_noisy else 'ground'
    
    gps_to_clean_gps = dict(GPSLat='clean_y', GPSLon='clean_x', Orientation='clean_heading')
    clean_gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
        colname_map=gps_to_clean_gps)
    
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(args.input_dir)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    slength = len(combined_frame['i'])
    empty = [np.nan for i in range(slength)]
    combined_frame['clean_x'] = empty
    combined_frame['clean_y'] = empty
    combined_frame['clean_heading'] = empty
    if args.max_time is not None:
        combined_frame = combined_frame[combined_frame.index < args.max_time]
    
    clean_gps_frame = None
    if args.clean_dir is not None:
        clean_gps_frame = vs.read_frame(dirname=args.clean_dir, **clean_gps_frame_config)
        for i in range(len(clean_gps_frame)):
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_x'] = clean_gps_frame.irow(i)['clean_x']
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_y'] = clean_gps_frame.irow(i)['clean_y']
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_heading'] = clean_gps_frame.irow(i)['clean_heading']
    return combined_frame, clean_gps_frame, dataset_name

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

print "Loading data"
# set_trace()
combined_frame, clean_gps_frame, dataset_name = read_combined_frame()

xlim = (-10, 10)
ylim = (-5, 5)
#xlim, ylim = get_lims(clean_gps_frame)

print "Set plot limits: " + str((xlim, ylim))

out_cols = ['SLAMGPSTime', 'SLAMLat', 'SLAMLon']

# Run the simple random walk solution.
def runRandomWalk():

    # Parameters for the random walk prior with Gaussian steps.
    noisy_gps_stds = dict(x=0.05, y=0.05, heading=0.01)

    ripl = venture.shortcuts.make_church_prime_ripl()

    row_num = min(args.frames, len(combined_frame))
    print "Using %d row" % row_num
    row_is = range(row_num)

    gps_frame_count = 0

    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []

    out_rows = []

  # For each row...
    for row_i in row_is:
        with Timer('row %s' % row_i) as t:
            combined_frame_row = combined_frame.irow(row_i)
            # set_trace()
            clean_gps = (combined_frame_row['clean_x'], combined_frame_row['clean_y'], combined_frame_row['clean_heading'])
                  
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
                    plot_pose(dataset_name + "_raw_%s.png" % gps_frame_count, xlim, ylim, xs=xs, ys=ys, headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
      
        times.append(t.elapsed)

    print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
    if args.plot:
        # Make the mp4 movie.
        mp4_name = dataset_name + '.mp4'
        template_str = dataset_name + '_raw_%1d.png'
        os.system('avconv -y -r 15 -i %s %s' % (template_str, mp4_name))
  
    return out_rows

def runApproach2():
    '''
    Run approach 2 as outlined in the document
    '''
    # Parameters for the random walk prior with Gaussian steps.
    noisy_gps_stds = dict(heading=0.01)
    k = args.window_size
  
    ripl = venture.shortcuts.make_church_prime_ripl()

    row_num = min(args.frames, len(combined_frame))
    print "Using %d row" % row_num
    row_is = range(row_num)

    gps_frame_count = 0

    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []

    out_rows = []
    for row_i in row_is:
        T = row_i
        with Timer('row %s' % T) as t:
            combined_frame_row = combined_frame.irow(T)

            clean_gps = (combined_frame_row['clean_x'], combined_frame_row['clean_y'], combined_frame_row['clean_heading'])
            xs = []
            ys = []
            headings = []
            x_datas = []
            y_datas = []

            if T is 0:
                # make model assumptions
                ripl.assume("x0", "(normal 0 1)", label="lx0")
                ripl.assume("y0", "(normal 0 1)",label="ly0")
                ripl.assume("noisy_gps_x_std", "(gamma 1 1)")
                ripl.assume("noisy_gps_y_std", "(gamma 1 1)")
                ripl.assume("heading0", "(uniform_continuous -3.14 3.14)")

            else:
                # set_trace()
                # assume x value given previous state
                ripl.assume("x%i"%T, "(normal x%i 0.1)" % (T-1), "lx%i"%T)
                ripl.assume("y%i"%T, "(normal y%i 0.1)" % (T-1), "ly%i"%T)
                ripl.assume("heading%i"%T, "(normal heading%i 0.1)" % (T-1))
                if T >= (k - 1):
                    ripl.freeze("lx%i"%(T-k+1))
                    ripl.freeze("ly%i"%(T-k+1))
                    # forget the observations if they exist
                    if not np.isnan(combined_frame.irow(T-k+1)['x'])
                        ripl.forget("x_data%i"%(T-k+1))
                        ripl.forget("y_data%i"%(T-k+1))

                if T >= k:
                    ripl.forget("lx%i"%(T-k))
                    ripl.forget("ly%i"%(T-k))

                print ripl.list_directives()[-5:],'\n'

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
                    plot_pose(dataset_name + "_raw_%s.png" % gps_frame_count, xlim, ylim, xs=xs, ys=ys,
                              headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
      
        times.append(t.elapsed)

    print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
    if args.plot:
        # Make the mp4 movie.
        mp4_name = dataset_name + '.mp4'
        template_str = dataset_name + '_raw_%1d.png'
        os.system('avconv -y -r 15 -b 1800 -i %s %s' % (template_str, mp4_name))
  
    return out_rows

def runApproach3():
    pass


approaches = dict(random_walk = runRandomWalk,
                  version_2 = runApproach2,
                  version_3 = runApproach3)
approach = approaches[args.version]

def ensure(path):
    path = path[:path.rfind('/')]
    if not os.path.exists(path):
        os.makedirs(path)

def writeCSV(filename, cols, rows):
    with open(filename, 'w') as f:
        f.write(','.join(cols) + '\n')
        for row in rows:
            f.write(','.join(map(str, row)) + '\n')


out_rows = approach()
out_file = '%s/slam_out_path.csv' % args.output_dir
ensure(out_file)
writeCSV(out_file, out_cols, out_rows)

print "Wrote output to " + out_file

landmarks_cols = ['SLAMBeaconX','SLAMBeaconY']
landmarks_rows = [(0, 0)]
landmarks_file = '%s/slam_out_landmarks.csv' % args.output_dir
writeCSV(landmarks_file, landmarks_cols, landmarks_rows)

print "Wrote landmarks to " + landmarks_file

